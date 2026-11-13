"""Fixtures for the maintained coordinator/entity regression suite.

These tests construct integration classes directly and mock the cloud client.
They do not load an integration config entry or exercise a real boiler.
"""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import frame
import pytest_asyncio


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
