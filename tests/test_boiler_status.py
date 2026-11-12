"""Regression tests for homestatus-driven HVAC action and legacy fallback."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from homeassistant.components.climate.const import HVACAction
import pytest
from vaillant_netatmo_api import ApiException, HomeStatus, RoomStatus, SystemMode

from custom_components.vaillant_vsmart.boiler_status import resolve_boiler_statuses
from custom_components.vaillant_vsmart.climate import VaillantClimate
from custom_components.vaillant_vsmart.entity import VaillantCoordinator


def topology(legacy=True):
    """Build one known thermostat with two repeated home room records."""
    room = SimpleNamespace(id="room", module_ids=["thermostat"])
    homes = [SimpleNamespace(id="home", rooms=[room, room])]
    module = SimpleNamespace(
        id="thermostat", type="NAThermVaillant", boiler_status=legacy,
        therm_program_list=[], measured=SimpleNamespace(temperature=19.7),
    )
    devices = [SimpleNamespace(id="device", modules=[module], system_mode=SystemMode.WINTER)]
    statuses = {"home": {"room": RoomStatus("room", 19.8, 20.0, True)}}
    return homes, devices, statuses


@pytest.mark.parametrize("value", [False, True])
def test_module_id_matching_ignores_order_and_unrelated_modules(value):
    """Accept explicit False, and never use another module's state."""
    homes, devices, statuses = topology()
    homes[0].rooms.insert(0, SimpleNamespace(id="other-room", module_ids=["other"]))
    readings = {"home": {"other": not value, "thermostat": value}}
    assert resolve_boiler_statuses(homes, devices, statuses, readings) == {"thermostat": value}


def test_cross_home_ambiguity_is_not_resolved_by_order():
    """A thermostat claimed by two homes cannot use either home's reading."""
    homes, devices, statuses = topology()
    homes.append(SimpleNamespace(id="another-home", rooms=homes[0].rooms))
    assert resolve_boiler_statuses(
        homes, devices, statuses, {"home": {"thermostat": True}}
    ) == {}


def test_unreachable_room_or_failed_home_does_not_use_module_readings():
    """A failed optional endpoint cannot reuse earlier valid states."""
    homes, devices, statuses = topology()
    readings = {"home": {"thermostat": True}}
    assert resolve_boiler_statuses(homes, devices, {}, readings) == {}
    statuses["home"]["room"] = RoomStatus("room", 19.8, 20.0, False)
    assert resolve_boiler_statuses(homes, devices, statuses, readings) == {}


@pytest.mark.parametrize(
    ("current", "legacy", "expected"),
    [(True, False, HVACAction.HEATING), (False, True, HVACAction.IDLE),
     (None, True, HVACAction.HEATING), (None, False, HVACAction.IDLE)],
)
def test_hvac_action_prefers_current_boolean_and_falls_back_only_when_absent(
    current, legacy, expected
):
    """Reproduce both observed transitions with the legacy endpoint reversed."""
    _, devices, _ = topology(legacy)
    coordinator = MagicMock()
    coordinator.data = SimpleNamespace(
        devices={"device": devices[0]}, modules={"thermostat": devices[0].modules[0]},
        boiler_statuses={} if current is None else {"thermostat": current},
    )
    climate = VaillantClimate(coordinator, "device", "thermostat")
    assert climate.hvac_action == expected


@pytest.mark.parametrize("mode", [SystemMode.FROSTGUARD, SystemMode.SUMMER])
def test_off_modes_keep_precedence(mode):
    """The new data source must not override system OFF modes."""
    _, devices, _ = topology()
    devices[0].system_mode = mode
    coordinator = MagicMock()
    coordinator.data = SimpleNamespace(
        devices={"device": devices[0]}, modules={"thermostat": devices[0].modules[0]},
        boiler_statuses={"thermostat": True},
    )
    assert VaillantClimate(coordinator, "device", "thermostat").hvac_action == HVACAction.OFF


async def test_coordinator_single_request_and_fresh_fallback_after_failure(hass):
    """Use one snapshot per home; failed next polls must not retain True."""
    homes, devices, statuses = topology(legacy=False)
    client = MagicMock()
    client.async_get_homes_data = AsyncMock(return_value=homes)
    client.async_get_thermostats_data = AsyncMock(return_value=devices)
    client.async_get_measure = AsyncMock(return_value=[])
    client.async_get_home_status_snapshot = AsyncMock(side_effect=[
        HomeStatus(statuses["home"], {"thermostat": True}),
        HomeStatus(statuses["home"], {}),
        ApiException("optional endpoint unavailable", None, None),
    ])
    coordinator = VaillantCoordinator(hass, client)
    first = await coordinator._update_method()
    assert first.boiler_statuses == {"thermostat": True}
    assert first.room_temperatures == {"thermostat": 19.8}
    client.async_get_home_status_snapshot.assert_awaited_once_with("home")
    client.async_get_home_status.assert_not_called()

    second = await coordinator._update_method()
    assert second.boiler_statuses == {}
    assert second.room_temperatures == {"thermostat": 19.8}
    third = await coordinator._update_method()
    assert third.boiler_statuses == {}
    assert third.room_temperatures == {}
    assert first.boiler_statuses == {"thermostat": True}
    coordinator.async_set_updated_data(third)
    climate = VaillantClimate(coordinator, "device", "thermostat")
    assert climate.hvac_action == HVACAction.IDLE
    assert climate.native_current_temperature == 19.7


def test_debug_log_contains_only_indices_and_readings(caplog):
    """Neither account IDs nor module IDs are exposed by source diagnostics."""
    homes, devices, statuses = topology()
    with caplog.at_level("DEBUG", logger="custom_components.vaillant_vsmart.boiler_status"):
        resolve_boiler_statuses(homes, devices, statuses, {"home": {"thermostat": False}})
    assert "source=homestatus" in caplog.text
    assert "selected=False" in caplog.text
    assert "module_id" not in caplog.text
    assert "thermostat'" not in caplog.text
