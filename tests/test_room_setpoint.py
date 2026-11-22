"""A command shows in the refresh right after it, not one step later.

Right after a setstate write, getthermostatsdata can still return the previous
mode and target while homestatus already reports the new ones. The climate
entity reads mode and target from homestatus where usable and falls back to
getthermostatsdata field by field; the debug log reports the same selection.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from homeassistant.components.climate.const import HVACMode
import logging

import pytest
from vaillant_netatmo_api_ng import ApiException, HomeStatus, RoomStatus, SystemMode

from custom_components.vaillant_vsmart_ng.climate import VaillantClimate
from custom_components.vaillant_vsmart_ng.entity import VaillantCoordinator
from custom_components.vaillant_vsmart_ng.room_setpoint import (
    SOURCE_HOMESTATUS,
    SOURCE_LEGACY,
    RoomSetpoint,
    SelectedSetpoint,
    resolve_room_setpoints,
    select_climate_setpoint,
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


# Selection -------------------------------------------------------------------


def test_selection_uses_homestatus_for_known_mode_and_target():
    """manual/16.5 from homestatus wins over a stale legacy auto/16."""
    assert select_climate_setpoint(
        RoomSetpoint("manual", 16.5), legacy(manual=False, target=16.0)
    ) == SelectedSetpoint("manual", SOURCE_HOMESTATUS, 16.5, SOURCE_HOMESTATUS)


@pytest.mark.parametrize("room_setpoint", [
    None, RoomSetpoint("away", 12.0), RoomSetpoint("hg", 7.0),
], ids=["no-homestatus", "away", "frost-guard"])
def test_selection_unsupported_mode_takes_mode_and_target_from_legacy(room_setpoint):
    """An unsupported room mode is ignored entirely, target included."""
    assert select_climate_setpoint(
        room_setpoint, legacy(manual=True, target=17.0)
    ) == SelectedSetpoint("manual", SOURCE_LEGACY, 17.0, SOURCE_LEGACY)


def test_selection_missing_target_mixes_sources():
    """A known mode without a target: mode from homestatus, target from legacy."""
    assert select_climate_setpoint(
        RoomSetpoint("manual", None), legacy(manual=False, target=16.0)
    ) == SelectedSetpoint("manual", SOURCE_HOMESTATUS, 16.0, SOURCE_LEGACY)


def test_selection_legacy_target_prefers_estimated_setpoint():
    """The legacy target is est_setpoint_temp, else setpoint_temp."""
    reading = legacy(manual=False, target=16.0)
    reading.measured.est_setpoint_temp = None
    reading.measured.setpoint_temp = 15.0
    assert select_climate_setpoint(None, reading).temperature == 15.0


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


def setpoint_log_lines(caplog):
    """Return the coordinator's setpoint source log messages."""
    return [
        record.getMessage() for record in caplog.records
        if record.getMessage().startswith("Vaillant setpoint source:")
    ]


@pytest.mark.parametrize("room_status, legacy_reading, expected, entity_state", [
    (
        status("away", 12.0), legacy(manual=True, target=17.0),
        "mode_source=getthermostatsdata_fallback selected_mode=manual "
        "target_source=getthermostatsdata_fallback selected_target=17.0 "
        "homestatus_mode=away homestatus_target=12.0",
        (HVACMode.HEAT, 17.0),
    ),
    (
        status("manual", None), legacy(manual=False, target=16.0),
        "mode_source=homestatus selected_mode=manual "
        "target_source=getthermostatsdata_fallback selected_target=16.0 "
        "homestatus_mode=manual homestatus_target=None",
        (HVACMode.HEAT, 16.0),
    ),
    (
        status("manual", 16.5), legacy(manual=False, target=16.0),
        "mode_source=homestatus selected_mode=manual "
        "target_source=homestatus selected_target=16.5 "
        "homestatus_mode=manual homestatus_target=16.5",
        (HVACMode.HEAT, 16.5),
    ),
], ids=["unsupported-mode", "missing-target", "homestatus"])
async def test_coordinator_log_reports_the_climate_selection(
    hass, caplog, room_status, legacy_reading, expected, entity_state
):
    """The debug log names the source the climate entity actually used."""
    homes, _ = topology()
    devices = [SimpleNamespace(
        id="device", system_mode=SystemMode.WINTER, modules=[legacy_reading],
    )]
    client = MagicMock()
    client.async_get_homes_data = AsyncMock(return_value=homes)
    client.async_get_thermostats_data = AsyncMock(return_value=devices)
    client.async_get_measure = AsyncMock(return_value=[])
    client.async_get_home_status_snapshot = AsyncMock(
        return_value=HomeStatus({"room": room_status}, {})
    )
    coordinator = VaillantCoordinator(hass, client)

    with caplog.at_level(logging.DEBUG):
        data = await coordinator._update_method()

    assert setpoint_log_lines(caplog) == [
        "Vaillant setpoint source: thermostat_index=0 " + expected
    ]
    entity = climate(legacy_reading, data.room_setpoints)
    assert (entity.hvac_mode, entity.native_target_temperature) == entity_state
