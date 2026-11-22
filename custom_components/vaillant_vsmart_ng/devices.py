"""Device registry entries for Vaillant gateways and the modules behind them."""
from collections.abc import Iterable
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from vaillant_netatmo_api_ng import Device, Module

from .const import DOMAIN

# Home Assistant deprecated `via_device` (gone in 2027.8) for `via_device_id`, which
# older releases, back to the 2024.5 minimum in hacs.json, do not accept.
SUPPORTS_VIA_DEVICE_ID = "via_device_id" in dr.DeviceInfo.__annotations__


def _firmware_version(value: Any) -> str | None:
    """Return firmware metadata as a string, preserving unknown values."""

    return str(value) if value is not None else None


def gateway_device_info(device: Device) -> dict[str, Any]:
    """Return the device registry info for a gateway."""

    return {
        "identifiers": {(DOMAIN, device.id)},
        "name": device.station_name,
        "sw_version": _firmware_version(device.firmware),
        "manufacturer": device.type,
    }


def _find_gateway(
    hass: HomeAssistant, identifier: tuple[str, str], config_entry_id: str
) -> dr.DeviceEntry | None:
    """Return the gateway's registry entry, looked up within the config entry."""

    registry = dr.async_get(hass)
    # Newer releases deprecate async_get_device, as identifiers are only unique
    # within a config entry.
    if find_in_entry := getattr(registry, "async_get_device_by_identifier", None):
        return find_in_entry(identifier, config_entry_id)
    return registry.async_get_device(identifiers={identifier})


def module_device_info(
    hass: HomeAssistant, config_entry_id: str, device: Device, module: Module
) -> dict[str, Any]:
    """Return the device registry info for a module, linked to its gateway."""

    info = {
        "identifiers": {(DOMAIN, module.id)},
        "name": module.module_name,
        "sw_version": _firmware_version(module.firmware),
        "manufacturer": device.type,
    }
    gateway_identifier = (DOMAIN, device.id)
    if not SUPPORTS_VIA_DEVICE_ID:
        info["via_device"] = gateway_identifier
    elif gateway := _find_gateway(hass, gateway_identifier, config_entry_id):
        info["via_device_id"] = gateway.id
    return info


@callback
def async_register_gateways(
    hass: HomeAssistant, entry: ConfigEntry, devices: Iterable[Device]
) -> None:
    """Register every gateway, so modules can link to it whichever platform loads first."""

    registry = dr.async_get(hass)
    for device in devices:
        registry.async_get_or_create(
            config_entry_id=entry.entry_id, **gateway_device_info(device)
        )
