"""A command shows in the refresh right after it, not one step later.

Measured on 2026-11-22: 0.4 s after a setstate write, homestatus already
reported the new room mode and target while getthermostatsdata still returned
the previous ones (it caught up within 12 s). The climate entity reads mode
and target from homestatus and falls back to getthermostatsdata.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from homeassistant.components.climate.const import HVACMode
import pytest
from vaillant_netatmo_api_ng import ApiException, HomeStatus, RoomStatus, SystemMode

from custom_components.vaillant_vsmart_ng.climate import VaillantClimate
from custom_components.vaillant_vsmart_ng.entity import VaillantCoordinator
from custom_components.vaillant_vsmart_ng.room_setpoint import (
    RoomSetpoint,
    resolve_room_setpoints,
)


def status(mode, setpoint, reachable=True, room_id="room"):
    """Build a homestatus room as a library exposing therm_setpoint_mode parses it."""
    return SimpleNamespace(
        room_id=room_id,
        measured_temperature=19.0,
        setpoint_temperature=setpoint,
        reachable=reachable,
        setpoint_mode=mode,
        setpoint_end_time=1795350676 if mode == "manual" else None,
    )


def topology():
    """One thermostat in a home whose sync API repeats the room record."""
    room = SimpleNamespace(id="room", module_ids=["thermostat"])
    homes = [
        SimpleNamespace(id="empty-home", rooms=[SimpleNamespace(id="empty", module_ids=[])]),
        SimpleNamespace(id="home", rooms=[room, room]),
    ]
    devices = [SimpleNamespace(
        id="device",
        system_mode=SystemMode.WINTER,
        modules=[SimpleNamespace(id="thermostat", type="NAThermVaillant")],
    )]
    return homes, devices


def legacy(manual, target, away=False):
    """Build the getthermostatsdata reading of the thermostat."""
    return SimpleNamespace(
        id="thermostat",
        type="NAThermVaillant",
        therm_program_list=[],
        boiler_status=False,
        setpoint_manual=SimpleNamespace(setpoint_activate=manual),
        setpoint_away=SimpleNamespace(setpoint_activate=away),
        measured=SimpleNamespace(
            temperature=19.0, setpoint_temp=target, est_setpoint_temp=target
        ),
    )


def climate(reading, room_setpoints):
    """Climate entity on coordinator data from one refresh."""
    coordinator = MagicMock()
    coordinator.data = SimpleNamespace(
        modules={"thermostat": reading},
        room_setpoints=room_setpoints,
    )
    return VaillantClimate(coordinator, "device", "thermostat")


# Resolver --------------------------------------------------------------------


def test_room_setpoint_maps_to_its_thermostat_by_module_id():
    """Follow rooms[].module_ids, not the first home or room."""
    homes, devices = topology()
    result = resolve_room_setpoints(
        homes, devices, {"home": {"room": status("manual", 16.5)}}
    )
    assert result == {"thermostat": RoomSetpoint("manual", 16.5)}


def test_library_without_setpoint_mode_falls_back_to_legacy():
    """vaillant-netatmo-api-ng 0.3.0 RoomStatus has no setpoint_mode."""
    homes, devices = topology()
    result = resolve_room_setpoints(
        homes, devices, {"home": {"room": RoomStatus("room", 19.0, 16.5, True)}}
    )
    assert result == {}


@pytest.mark.parametrize(
    "room_status",
    [status("manual", 16.5, reachable=False), status(None, 16.5), status("", 16.5)],
    ids=["unreachable", "no-mode", "empty-mode"],
)
def test_unusable_room_status_falls_back_to_legacy(room_status):
    """Unreachable rooms and rooms without a mode are not used."""
    homes, devices = topology()
    assert resolve_room_setpoints(homes, devices, {"home": {"room": room_status}}) == {}


def test_missing_home_status_falls_back_to_legacy():
    """A failed homestatus request leaves nothing to resolve."""
    homes, devices = topology()
    assert resolve_room_setpoints(homes, devices, {}) == {}


def test_thermostat_in_two_disagreeing_rooms_falls_back_to_legacy():
    """Never pick one room by order."""
    homes, devices = topology()
    homes[1].rooms = [
        SimpleNamespace(id="living", module_ids=["thermostat"]),
        SimpleNamespace(id="study", module_ids=["thermostat"]),
    ]
    statuses = {"home": {
        "living": status("manual", 16.5, room_id="living"),
        "study": status("home", 16.0, room_id="study"),
    }}
    assert resolve_room_setpoints(homes, devices, statuses) == {}


def test_non_thermostat_modules_are_ignored():
    """Only NAThermVaillant modules get a room setpoint."""
    homes, devices = topology()
    devices[0].modules[0].type = "NAVaillant"
    assert resolve_room_setpoints(
        homes, devices, {"home": {"room": status("manual", 16.5)}}
    ) == {}


# Climate entity --------------------------------------------------------------


def test_set_temperature_shows_in_the_next_refresh():
    """The reported bug: set 16.5 in auto; legacy still says auto 16."""
    entity = climate(legacy(manual=False, target=16.0),
                     {"thermostat": RoomSetpoint("manual", 16.5)})
    assert entity.hvac_mode == HVACMode.HEAT
    assert entity.native_target_temperature == 16.5


def test_back_to_auto_shows_in_the_next_refresh():
    """Back to the schedule; legacy still says manual 16.5."""
    entity = climate(legacy(manual=True, target=16.5),
                     {"thermostat": RoomSetpoint("home", 16.0)})
    assert entity.hvac_mode == HVACMode.AUTO
    assert entity.native_target_temperature == 16.0


@pytest.mark.parametrize("room_setpoints", [
    {},
    {"thermostat": RoomSetpoint("away", 12.0)},
    {"thermostat": RoomSetpoint("hg", 7.0)},
], ids=["no-homestatus", "away", "frost-guard"])
def test_unknown_or_missing_room_mode_uses_legacy(room_setpoints):
    """Only the measured schedule/manual modes override getthermostatsdata."""
    entity = climate(legacy(manual=True, target=17.0), room_setpoints)
    assert entity.hvac_mode == HVACMode.HEAT
    assert entity.native_target_temperature == 17.0


def test_room_mode_without_setpoint_keeps_legacy_target():
    """A missing homestatus target does not hide the legacy one."""
    entity = climate(legacy(manual=False, target=16.0),
                     {"thermostat": RoomSetpoint("manual", None)})
    assert entity.hvac_mode == HVACMode.HEAT
    assert entity.native_target_temperature == 16.0


def test_coordinator_data_without_room_setpoints_uses_legacy():
    """Entities built on older coordinator data keep working."""
    coordinator = MagicMock()
    coordinator.data = SimpleNamespace(modules={"thermostat": legacy(True, 17.0)})
    entity = VaillantClimate(coordinator, "device", "thermostat")
    assert entity.hvac_mode == HVACMode.HEAT
    assert entity.native_target_temperature == 17.0


# Coordinator -----------------------------------------------------------------


async def test_coordinator_resolves_fresh_room_setpoints_every_refresh(hass):
    """Each refresh uses its own homestatus; a failed one falls back."""
    homes, _ = topology()
    devices = [SimpleNamespace(
        id="device", system_mode=SystemMode.WINTER,
        modules=[legacy(manual=False, target=16.0)],
    )]
    client = MagicMock()
    client.async_get_homes_data = AsyncMock(return_value=homes)
    client.async_get_thermostats_data = AsyncMock(return_value=devices)
    client.async_get_measure = AsyncMock(return_value=[])
    client.async_get_home_status_snapshot = AsyncMock(side_effect=[
        HomeStatus({"room": status("manual", 16.5)}, {}),
        ApiException("optional endpoint unavailable", None, None),
    ])
    coordinator = VaillantCoordinator(hass, client)

    first = await coordinator._update_method()
    assert first.room_setpoints == {"thermostat": RoomSetpoint("manual", 16.5)}
    client.async_get_home_status_snapshot.assert_awaited_once_with("home")

    second = await coordinator._update_method()
    assert second.room_setpoints == {}
