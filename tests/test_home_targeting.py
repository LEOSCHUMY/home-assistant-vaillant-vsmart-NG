"""Commands go to the home and room that hold the thermostat, never the first one."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from homeassistant.components.climate.const import PRESET_AWAY
from homeassistant.exceptions import HomeAssistantError
import pytest
from vaillant_netatmo_api_ng import Home, ThermMode, ThermSetpointMode

from custom_components.vaillant_vsmart_ng.climate import VaillantClimate
from custom_components.vaillant_vsmart_ng.home_targeting import target_home, target_room
from custom_components.vaillant_vsmart_ng.switch import VaillantHwbSwitch
from custom_components.vaillant_vsmart_ng.water_heater import (
    OPERATION_HEATING,
    VaillantWaterHeater,
)


def home(home_id: str, *rooms: tuple[str, list[str]]) -> Home:
    """Build a homesdata home; each room is a (room ID, module IDs) pair."""
    return Home(
        id=home_id,
        rooms=[{"id": room_id, "module_ids": module_ids} for room_id, module_ids in rooms],
    )


TWO_HOMES = [
    home("empty-home", ("empty-room", [])),
    home("home", ("living", ["other-thermostat"]), ("study", ["thermostat"])),
]


def test_module_targets_its_own_home_and_room_not_the_first():
    """Several homes and rooms: follow the room that lists the module."""
    assert target_home(TWO_HOMES, ["thermostat"]).id == "home"
    assert target_room(TWO_HOMES, "thermostat").id == "study"


def test_device_targets_the_home_of_its_modules():
    """The relay is not in rooms[].module_ids; its thermostats place it."""
    assert target_home(TWO_HOMES, ["thermostat", "other-thermostat"]).id == "home"


def test_repeated_room_records_are_one_placement():
    """The sync API can repeat a room record; that is not an ambiguity."""
    homes = [home("home", ("room", ["thermostat"]), ("room", ["thermostat"]))]
    assert target_home(homes, ["thermostat"]).id == "home"
    assert target_room(homes, "thermostat").id == "room"


@pytest.mark.parametrize("rooms", [1, 2], ids=["one-record", "repeated-record"])
def test_single_home_and_room_without_topology_is_unambiguous(rooms):
    """Accounts without module_ids keep working when there is one choice."""
    homes = [home("home", *[("room", [])] * rooms)]
    assert target_home(homes, ["thermostat"]).id == "home"
    assert target_room(homes, "thermostat").id == "room"


def test_single_home_with_several_unassigned_rooms_has_no_target_room():
    """Never fall back to room order."""
    homes = [home("home", ("living", []), ("study", []))]
    assert target_home(homes, ["thermostat"]).id == "home"
    assert target_room(homes, "thermostat") is None


def test_topology_that_lists_another_module_has_no_target():
    """Present topology without this module is a mismatch, not missing data."""
    homes = [home("home", ("room", ["another-thermostat"]))]
    assert target_home(homes, ["missing-thermostat"]) is None
    assert target_room(homes, "missing-thermostat") is None


def test_module_in_two_rooms_of_one_home_has_no_target_room():
    """The home is clear, but a room-targeted command must not guess."""
    homes = [home("home", ("living", ["thermostat"]), ("study", ["thermostat"]))]
    assert target_home(homes, ["thermostat"]).id == "home"
    assert target_room(homes, "thermostat") is None


@pytest.mark.parametrize(
    "homes",
    [
        [home("home", ("room", [])), home("other-home", ("other-room", []))],
        [home("home", ("room", ["thermostat"])),
         home("other-home", ("other-room", ["thermostat"]))],
        [],
    ],
    ids=["unassigned", "claimed-by-two-homes", "no-homes"],
)
def test_ambiguous_placement_has_no_target(homes):
    """Never fall back to home order."""
    assert target_home(homes, ["thermostat"]) is None
    assert target_room(homes, "thermostat") is None


def coordinator_for(homes: list[Home]) -> MagicMock:
    """Build coordinator data for one boiler with one thermostat."""
    thermostat = SimpleNamespace(id="thermostat")
    device = SimpleNamespace(
        id="device", modules=[thermostat], setpoint_default_duration=60
    )
    client = MagicMock()
    client.async_set_state_for_room = AsyncMock()
    client.async_set_home_data = AsyncMock()
    client.async_set_state_for_module = AsyncMock()
    coordinator = MagicMock()
    coordinator.async_request_refresh = AsyncMock()
    coordinator.data = SimpleNamespace(
        client=client,
        homes={home.id: home for home in homes},
        devices={"device": device},
        modules={"thermostat": thermostat},
    )
    return coordinator


async def test_climate_commands_target_the_thermostat_home_and_room():
    """Setpoint and preset writes go to the thermostat's own home and room."""
    coordinator = coordinator_for(TWO_HOMES)
    climate = VaillantClimate(coordinator, "device", "thermostat")

    await climate.async_set_temperature(temperature=20.5)
    await climate.async_set_preset_mode(PRESET_AWAY)

    args = coordinator.data.client.async_set_state_for_room.await_args.args
    assert args[:3] == ("home", "study", ThermSetpointMode.MANUAL)
    args = coordinator.data.client.async_set_home_data.await_args.args
    assert args[0] == "home"
    assert args[2] == ThermMode.AWAY


async def test_boiler_commands_target_the_home_of_its_thermostat():
    """Hot water boost and operation mode writes go to the boiler's home."""
    coordinator = coordinator_for(TWO_HOMES)

    await VaillantHwbSwitch(coordinator, "device").async_turn_on()
    await VaillantWaterHeater(coordinator, "device").async_set_operation_mode(
        OPERATION_HEATING
    )

    coordinator.data.client.async_set_state_for_module.assert_awaited_once_with(
        "home", "device", True
    )
    assert coordinator.data.client.async_set_home_data.await_args.args[0] == "home"


async def test_ambiguous_target_is_reported_before_any_write():
    """Raise a clear error instead of writing to an arbitrary home."""
    coordinator = coordinator_for(
        [home("home", ("room", [])), home("other-home", ("other-room", []))]
    )

    with pytest.raises(HomeAssistantError, match="exactly one room"):
        await VaillantClimate(coordinator, "device", "thermostat").async_set_temperature(
            temperature=20.5
        )
    with pytest.raises(HomeAssistantError, match="exactly one room"):
        await VaillantHwbSwitch(coordinator, "device").async_turn_on()

    coordinator.data.client.async_set_state_for_room.assert_not_awaited()
    coordinator.data.client.async_set_state_for_module.assert_not_awaited()
    coordinator.async_request_refresh.assert_not_awaited()


async def test_topology_that_lists_another_module_is_rejected_before_any_write():
    """A single home and room is no fallback when it lists another thermostat."""
    coordinator = coordinator_for([home("home", ("room", ["another-thermostat"]))])
    climate = VaillantClimate(coordinator, "device", "thermostat")

    with pytest.raises(HomeAssistantError, match="exactly one room"):
        await climate.async_set_temperature(temperature=20.5)
    with pytest.raises(HomeAssistantError, match="exactly one room"):
        await climate.async_set_preset_mode(PRESET_AWAY)
    with pytest.raises(HomeAssistantError, match="exactly one room"):
        await VaillantHwbSwitch(coordinator, "device").async_turn_on()

    coordinator.data.client.async_set_state_for_room.assert_not_awaited()
    coordinator.data.client.async_set_home_data.assert_not_awaited()
    coordinator.data.client.async_set_state_for_module.assert_not_awaited()
    coordinator.async_request_refresh.assert_not_awaited()


async def test_module_in_two_rooms_rejects_room_commands_before_any_write():
    """A thermostat listed in two rooms of one home gets no room setpoint."""
    coordinator = coordinator_for(
        [home("home", ("living", ["thermostat"]), ("study", ["thermostat"]))]
    )

    with pytest.raises(HomeAssistantError, match="exactly one room"):
        await VaillantClimate(coordinator, "device", "thermostat").async_set_temperature(
            temperature=20.5
        )

    coordinator.data.client.async_set_state_for_room.assert_not_awaited()
    coordinator.async_request_refresh.assert_not_awaited()
