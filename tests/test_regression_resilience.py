"""Regression tests for API and measurement failure handling."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from homeassistant.exceptions import HomeAssistantError
import pytest
from vaillant_netatmo_api import ApiException, MeasurementType

from custom_components.vaillant_vsmart.entity import VaillantCoordinator
from custom_components.vaillant_vsmart.sensor import (
    VaillantDurationSensor,
    VaillantEnergySensor,
)
from custom_components.vaillant_vsmart.switch import (
    VaillantHwbSwitch,
    VaillantScheduleSwitch,
)


def api_error(message):
    """Build an API exception with the constructor required by the client library."""
    return ApiException(message, None, None)


async def test_measurement_api_error_does_not_abort_coordinator_refresh(hass):
    """A failure for one measurement type must not discard the other data."""
    module = SimpleNamespace(id="module", therm_program_list=[])
    device = SimpleNamespace(id="device", modules=[module])
    client = MagicMock()
    client.async_get_homes_data = AsyncMock(return_value=[])
    client.async_get_thermostats_data = AsyncMock(return_value=[device])
    failed_type = MeasurementType.SUM_ENERGY_GAS_HEATING

    async def get_measure(device_id, module_id, measurement_type, scale, date_begin):
        if measurement_type == failed_type:
            raise api_error("measurement endpoint unavailable")
        return [SimpleNamespace(value=[12])]

    client.async_get_measure = AsyncMock(side_effect=get_measure)
    data = await VaillantCoordinator(hass, client)._update_method()

    assert data.devices == {"device": device}
    assert data.measurements[("device", "module", failed_type)] == []
    assert data.measurements[("device", "module", MeasurementType.SUM_ENERGY_GAS_WATER)]


@pytest.mark.parametrize(
    ("sensor_class", "measurement_type", "measurements"),
    [
        (VaillantEnergySensor, MeasurementType.SUM_ENERGY_GAS_HEATING, {}),
        (VaillantEnergySensor, MeasurementType.SUM_ENERGY_GAS_HEATING,
         {("device", "module", MeasurementType.SUM_ENERGY_GAS_HEATING): []}),
        (VaillantDurationSensor, MeasurementType.SUM_BOILER_ON, {}),
        (VaillantDurationSensor, MeasurementType.SUM_BOILER_ON,
         {("device", "module", MeasurementType.SUM_BOILER_ON): []}),
    ],
)
def test_measurement_sensor_returns_none_for_missing_or_empty_data(
    sensor_class, measurement_type, measurements
):
    """Missing and empty measurement lists must produce an unavailable value."""
    coordinator = MagicMock()
    coordinator.data = SimpleNamespace(
        client=MagicMock(),
        devices={"device": SimpleNamespace(id="device")},
        modules={"module": SimpleNamespace(id="module")},
        measurements=measurements,
    )
    sensor = sensor_class(coordinator, "device", "module", measurement_type)
    assert sensor.native_value is None


async def test_hot_water_boost_api_error_is_reported_and_not_refreshed():
    """A failed boost command must raise a HA error without refreshing."""
    client = MagicMock()
    client.async_set_state_for_module = AsyncMock(
        side_effect=api_error("command failed")
    )
    coordinator = MagicMock()
    coordinator.data = SimpleNamespace(
        client=client,
        homes={"home": SimpleNamespace(id="home")},
    )
    coordinator.async_request_refresh = AsyncMock()
    switch = VaillantHwbSwitch(coordinator, "device")

    with pytest.raises(HomeAssistantError, match="Unable to enable hot water boost"):
        await switch.async_turn_on()
    coordinator.async_request_refresh.assert_not_awaited()


async def test_schedule_switch_cannot_be_turned_off():
    """Schedules are changed by selecting another schedule, not switched off."""
    switch = VaillantScheduleSwitch(MagicMock(), "device", "module", "program")
    with pytest.raises(HomeAssistantError, match="cannot be switched off"):
        await switch.async_turn_off()
