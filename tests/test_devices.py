"""Tests for linking module devices to their gateway in the device registry."""
from types import SimpleNamespace

from homeassistant.helpers import device_registry as dr

from custom_components.vaillant_vsmart_ng.const import DOMAIN
from custom_components.vaillant_vsmart_ng.devices import (
    SUPPORTS_VIA_DEVICE_ID,
    async_register_gateways,
    module_device_info,
)

from .conftest import CONFIG_ENTRY_ID

GATEWAY = SimpleNamespace(
    id="gateway", station_name="Boiler", type="NAPlug", firmware=1
)
MODULE = SimpleNamespace(id="module", module_name="Thermostat", firmware=2)


async def test_module_device_is_linked_to_registered_gateway(hass, device_registry):
    """A module registers under its gateway without the deprecated via_device."""
    async_register_gateways(hass, SimpleNamespace(entry_id=CONFIG_ENTRY_ID), [GATEWAY])
    [gateway] = [
        device for device in dr.async_entries_for_config_entry(device_registry, CONFIG_ENTRY_ID)
        if (DOMAIN, "gateway") in device.identifiers
    ]

    info = module_device_info(hass, CONFIG_ENTRY_ID, GATEWAY, MODULE)
    module = device_registry.async_get_or_create(config_entry_id=CONFIG_ENTRY_ID, **info)

    assert module.via_device_id == gateway.id
    assert ("via_device" not in info) == SUPPORTS_VIA_DEVICE_ID


async def test_module_device_without_registered_gateway_has_no_link(hass, device_registry):
    """An unknown gateway leaves the module unlinked instead of failing."""
    info = module_device_info(hass, CONFIG_ENTRY_ID, GATEWAY, MODULE)
    module = device_registry.async_get_or_create(config_entry_id=CONFIG_ENTRY_ID, **info)

    assert module.via_device_id is None
    assert "via_device_id" not in info
