"""Vaillant vSMART entity classes."""
from datetime import timedelta, datetime
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from vaillant_netatmo_api import (
    ApiException,
    Home,
    Room,
    Device,
    Module,
    Program,
    ThermostatClient,
    RequestUnauthorizedException,
    MeasurementScale,
    MeasurementItem,
    MeasurementType,
)

from .const import DOMAIN, SUPPORTED_ENERGY_MEASUREMENT_TYPES, SUPPORTED_DURATION_MEASUREMENT_TYPES
from .room_temperature import resolve_room_temperatures

UPDATE_INTERVAL = timedelta(minutes=5)

_LOGGER: logging.Logger = logging.getLogger(__package__)


def _firmware_version(value: Any) -> str | None:
    """Return firmware metadata as a string, preserving unknown values."""

    return str(value) if value is not None else None


class VaillantData:
    """Class holding data which coordinator provides to the entity."""

    def __init__(self, client: ThermostatClient, homes: list[Home], devices: list[Device],
                 measurements: dict[(str, str, MeasurementType), MeasurementItem],
                 room_temperatures: dict[str, float] | None = None) -> None:
        """Initialize."""

        self.client = client
        self.homes = {home.id: home for home in homes}
        self.rooms = {
            room.id: room for home in homes for room in home.rooms
        }
        self.devices = {device.id: device for device in devices}
        self.modules = {
            module.id: module for device in devices for module in device.modules
        }
        self.programs = {
            program.id: program
            for device in devices
            for module in device.modules
            for program in module.therm_program_list
        }
        self.measurements = measurements
        # Keyed by thermostat module ID; no dependency on rooms[0] ordering.
        self.room_temperatures = room_temperatures if room_temperatures is not None else {}


class VaillantCoordinator(DataUpdateCoordinator[VaillantData]):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, client: ThermostatClient) -> None:
        """Initialize."""

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_method=self._update_method,
            update_interval=UPDATE_INTERVAL,
        )

        self._client = client

    async def _update_method(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """

        try:
            homes = await self._client.async_get_homes_data()
            devices = await self._client.async_get_thermostats_data()

            # Homestatus is optional: failure must not affect boiler controls
            # or other entities. Legacy measured.temperature remains fallback.
            statuses_by_home = {}
            for home in homes:
                if not home.id or not any(room.module_ids for room in home.rooms):
                    continue
                try:
                    statuses_by_home[home.id] = (
                        await self._client.async_get_home_status(home.id)
                    )
                except (ApiException, ValueError) as ex:
                    # Do not log exception bodies; they may include account IDs.
                    _LOGGER.warning(
                        "Vaillant homestatus unavailable (%s); using legacy temperatures",
                        type(ex).__name__,
                    )
            room_temperatures = resolve_room_temperatures(
                homes, devices, statuses_by_home
            )

            # Diagnostic only: the climate entity uses precisely this lookup.
            # Log numeric temperatures and positional indices, never IDs,
            # account metadata, credentials, or complete API payloads.
            if _LOGGER.isEnabledFor(logging.DEBUG):
                thermostat_index = 0
                for device in devices:
                    for module in device.modules:
                        if getattr(module, "type", None) != "NAThermVaillant":
                            continue
                        legacy_temperature = getattr(
                            getattr(module, "measured", None), "temperature", None
                        )
                        status_temperature = room_temperatures.get(module.id)
                        source = (
                            "homestatus"
                            if status_temperature is not None
                            else "getthermostatsdata_fallback"
                        )
                        chosen_temperature = (
                            status_temperature
                            if status_temperature is not None
                            else legacy_temperature
                        )
                        _LOGGER.debug(
                            "Vaillant room temperature source: thermostat_index=%d "
                            "source=%s homestatus_temperature=%s "
                            "legacy_temperature=%s selected_temperature=%s",
                            thermostat_index,
                            source,
                            status_temperature,
                            legacy_temperature,
                            chosen_temperature,
                        )
                        thermostat_index += 1

            date_begin = datetime.now() - timedelta(days=1)
            measurements = {}
            for device in devices:
                for module in device.modules:
                    for measurement_type in (
                        SUPPORTED_ENERGY_MEASUREMENT_TYPES
                        + SUPPORTED_DURATION_MEASUREMENT_TYPES
                    ):
                        try:
                            measurements[(device.id, module.id, measurement_type)] = (
                                await self._client.async_get_measure(
                                    device.id,
                                    module.id,
                                    measurement_type,
                                    MeasurementScale.DAY,
                                    date_begin,
                                )
                            )
                        except RequestUnauthorizedException:
                            raise
                        except ApiException as ex:
                            _LOGGER.warning(
                                "Unable to fetch %s measurements for module %s: %s",
                                measurement_type,
                                module.id,
                                ex,
                            )
                            measurements[(device.id, module.id, measurement_type)] = []

            return VaillantData(
                self._client, homes, devices, measurements, room_temperatures
            )
        except RequestUnauthorizedException as ex:
            raise ConfigEntryAuthFailed from ex
        except ApiException as ex:
            _LOGGER.exception(ex)
            raise UpdateFailed(f"Error communicating with API: {ex}") from ex


class VaillantDeviceEntity(CoordinatorEntity[VaillantData]):
    """Base class for Vaillant device entities."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[VaillantData],
        device_id: str,
    ):
        """Initialize."""

        super().__init__(coordinator)

        self._device_id = device_id

    @property
    def _client(self) -> ThermostatClient:
        """Retrun the instance of the client which enables HTTP communication with the API."""

        return self.coordinator.data.client

    @property
    def _home(self) -> Home:
        """Return the device which this entity represents."""

        # TODO: Remove this hack
        # We assume there is only one home and one room
        # This assumption will be removed when we switch entirely to using new APIs
        for id in self.coordinator.data.homes:
            return self.coordinator.data.homes[id]

    @property
    def _room(self) -> Room:
        """Return the device which this entity represents."""

        # TODO: Remove this hack
        # We assume there is only one home and one room
        # This assumption will be removed when we switch entirely to using new APIs
        for id in self.coordinator.data.rooms:
            return self.coordinator.data.rooms[id]

    @property
    def _device(self) -> Device:
        """Return the device which this entity represents."""

        return self.coordinator.data.devices[self._device_id]

    @property
    def unique_id(self) -> str:
        """Return a unique ID to use for this entity."""

        return self._device.id

    @property
    def has_entity_name(self) -> bool:
        """Return if entity is using new entity naming conventions."""

        return True

    @property
    def device_info(self) -> dict[str, Any]:
        """Return all device info available for this entity."""

        return {
            "identifiers": {(DOMAIN, self._device.id)},
            "name": self._device.station_name,
            "sw_version": _firmware_version(self._device.firmware),
            "manufacturer": self._device.type,
        }


class VaillantModuleEntity(CoordinatorEntity[VaillantData]):
    """Base class for Vaillant module entities."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[VaillantData],
        device_id: str,
        module_id: str,
    ):
        """Initialize."""

        super().__init__(coordinator)

        self._device_id = device_id
        self._module_id = module_id

    @property
    def _client(self) -> ThermostatClient:
        """Retrun the instance of the client which enables HTTP communication with the API."""

        return self.coordinator.data.client

    @property
    def _home(self) -> Home:
        """Return the device which this entity represents."""

        # TODO: Remove this hack
        # We assume there is only one home and one room
        # This assumption will be removed when we switch entirely to using new APIs
        for id in self.coordinator.data.homes:
            return self.coordinator.data.homes[id]

    @property
    def _room(self) -> Room:
        """Return the device which this entity represents."""

        # TODO: Remove this hack
        # We assume there is only one home and one room
        # This assumption will be removed when we switch entirely to using new APIs
        for id in self.coordinator.data.rooms:
            return self.coordinator.data.rooms[id]

    @property
    def _device(self) -> Device:
        """Return the device which this entity represents."""

        return self.coordinator.data.devices[self._device_id]

    @property
    def _module(self) -> Module:
        """Return the module which this entity represents."""

        return self.coordinator.data.modules[self._module_id]

    @property
    def unique_id(self) -> str:
        """Return a unique ID to use for this entity."""

        return self._module.id

    @property
    def has_entity_name(self) -> bool:
        """Return if entity is using new entity naming conventions."""

        return True

    @property
    def device_info(self) -> dict[str, Any]:
        """Return all device info available for this entity."""

        return {
            "identifiers": {(DOMAIN, self._module.id)},
            "name": self._module.module_name,
            "sw_version": _firmware_version(self._module.firmware),
            "manufacturer": self._device.type,
            "via_device": (DOMAIN, self._device.id),
        }


class VaillantProgramEntity(CoordinatorEntity[VaillantData]):
    """Base class for Vaillant program entities."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[VaillantData],
        device_id: str,
        module_id: str,
        program_id: str,
    ):
        """Initialize."""

        super().__init__(coordinator)

        self._device_id = device_id
        self._module_id = module_id
        self._program_id = program_id

    @property
    def _client(self) -> ThermostatClient:
        """Retrun the instance of the client which enables HTTP communication with the API."""

        return self.coordinator.data.client

    @property
    def _device(self) -> Device:
        """Return the device which this entity represents."""

        return self.coordinator.data.devices[self._device_id]

    @property
    def _module(self) -> Module:
        """Return the module which this entity represents."""

        return self.coordinator.data.modules[self._module_id]

    @property
    def _program(self) -> Program:
        """Return the program which this entity represents."""

        return self.coordinator.data.programs[self._program_id]

    @property
    def unique_id(self) -> str:
        """Return a unique ID to use for this entity."""

        return self._program.id

    @property
    def has_entity_name(self) -> bool:
        """Return if entity is using new entity naming conventions."""

        return True

    @property
    def device_info(self) -> dict[str, Any]:
        """Return all device info available for this entity."""

        return {
            "identifiers": {(DOMAIN, self._module.id)},
            "name": self._module.module_name,
            "sw_version": _firmware_version(self._module.firmware),
            "manufacturer": self._device.type,
            "via_device": (DOMAIN, self._device.id),
        }


class VaillantMeasurementEntity(CoordinatorEntity[VaillantData]):
    """Base class for Vaillant measurement entities."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[VaillantData],
        device_id: str,
        module_id: str,
        measurement_type: MeasurementType,
    ):
        """Initialize."""

        super().__init__(coordinator)

        self._device_id = device_id
        self._module_id = module_id
        self._measurement_type = measurement_type

    @property
    def _client(self) -> ThermostatClient:
        """Retrun the instance of the client which enables HTTP communication with the API."""

        return self.coordinator.data.client

    @property
    def _device(self) -> Device:
        """Return the device which this entity represents."""

        return self.coordinator.data.devices[self._device_id]

    @property
    def _module(self) -> Module:
        """Return the module which this entity represents."""

        return self.coordinator.data.modules[self._module_id]

    @property
    def _measurement(self) -> MeasurementItem | None:
        """Return the measurement which this entity represents."""

        measurements = self.coordinator.data.measurements.get(
            (self._device_id, self._module_id, self._measurement_type), []
        )
        if not measurements:
            return None

        return measurements[-1]

    @property
    def unique_id(self) -> str:
        """Return a unique ID to use for this entity."""

        return f"{self._module.id}_{self._measurement_type}"

    @property
    def has_entity_name(self) -> bool:
        """Return if entity is using new entity naming conventions."""

        return True

    @property
    def device_info(self) -> dict[str, Any]:
        """Return all device info available for this entity."""

        return {
            "identifiers": {(DOMAIN, self._module.id)},
            "name": self._module.module_name,
            "sw_version": _firmware_version(self._module.firmware),
            "manufacturer": self._device.type,
            "via_device": (DOMAIN, self._device.id),
        }
