"""Fixtures for the maintained coordinator/entity regression suite.

These tests construct integration classes directly and mock the cloud client.
They do not load an integration config entry or exercise a real boiler.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, frame
import pytest_asyncio

from custom_components.vaillant_vsmart_ng.const import DOMAIN

CONFIG_ENTRY_ID = "entry"


@pytest_asyncio.fixture
async def hass(tmp_path):
    """Provide a real HA instance without a version-coupled third-party harness."""
    instance = HomeAssistant(str(tmp_path))
    if setup_frame := getattr(frame, "async_setup", None):
        setup_frame(instance)
    try:
        yield instance
    finally:
        await instance.async_stop(force=True)
        await instance.async_block_till_done()


@pytest_asyncio.fixture
async def device_registry(hass):
    """Provide a loaded device registry with one config entry known to HA."""
    entry = SimpleNamespace(
        entry_id=CONFIG_ENTRY_ID, domain=DOMAIN, title="Vaillant", subentries={},
        disabled_by=None,
    )
    hass.config_entries = MagicMock()
    hass.config_entries.async_get_entry.side_effect = (
        lambda entry_id: entry if entry_id == entry.entry_id else None
    )
    if setup_registry := getattr(dr, "async_setup", None):
        setup_registry(hass)
    await dr.async_load(hass)
    return dr.async_get(hass)
