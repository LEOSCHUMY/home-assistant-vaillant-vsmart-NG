"""Tests for the homestatus-to-thermostat mapping without HA dependencies."""

from types import SimpleNamespace as Obj
from pathlib import Path
import importlib.util

# Load the pure helper without importing HA's custom component __init__.py.
source = Path(__file__).resolve().parents[1] / "custom_components" / "vaillant_vsmart" / "room_temperature.py"
spec = importlib.util.spec_from_file_location("vaillant_room_temperature", source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
resolve_room_temperatures = module.resolve_room_temperatures


def home(home_id, *rooms):
    """Build a minimal home fixture."""
    return Obj(id=home_id, rooms=list(rooms))


def room(room_id, *modules):
    """Build a minimal room fixture."""
    return Obj(id=room_id, module_ids=list(modules))


def device(*modules):
    """Build a minimal device fixture."""
    return Obj(modules=[Obj(id=module_id, type=module_type) for module_id, module_type in modules])


def status(temp, reachable=True):
    """Build a minimal room status fixture."""
    return Obj(measured_temperature=temp, reachable=reachable)


def test_one_thermostat_one_room():
    """Map a single room to its thermostat."""
    result = resolve_room_temperatures(
        [home("h1", room("r1", "therm1"))],
        [device(("therm1", "NAThermVaillant"))],
        {"h1": {"r1": status(19.5)}},
    )
    assert result == {"therm1": 19.5}


def test_multiple_rooms_map_to_their_own_thermostats():
    """Match temperatures independently across rooms."""
    result = resolve_room_temperatures(
        [home("h1", room("r1", "therm1"), room("r2", "therm2"))],
        [device(("therm1", "NAThermVaillant"), ("therm2", "NAThermVaillant"))],
        {"h1": {"r1": status(18.5), "r2": status(20.0)}},
    )
    assert result == {"therm1": 18.5, "therm2": 20.0}


def test_missing_unreachable_and_nonthermostat_modules_fall_back():
    """Ignore readings without valid thermostat mappings."""
    result = resolve_room_temperatures(
        [home("h1", room("r1", "therm1"), room("r2", "therm2"), room("r3", "bridge"))],
        [device(("therm1", "NAThermVaillant"),
                ("therm2", "NAThermVaillant"), ("bridge", "NAVaillant"))],
        {"h1": {"r1": status(None), "r2": status(20.0, False), "r3": status(19.0)}},
    )
    assert result == {}


def test_conflicting_mapping_stays_on_fallback_even_after_third_record():
    """Retain fallback after detecting a conflicting mapping."""
    result = resolve_room_temperatures(
        [home("h1", room("r1", "therm1"), room("r2", "therm1"),
              room("r3", "therm1"))],
        [device(("therm1", "NAThermVaillant"))],
        {"h1": {"r1": status(18.0), "r2": status(19.0), "r3": status(19.0)}},
    )
    assert result == {}


def test_unavailable_home_does_not_block_another_home():
    """Keep unaffected homes usable when status is missing."""
    result = resolve_room_temperatures(
        [home("h1", room("r1", "therm1")), home("h2", room("r2", "therm2"))],
        [device(("therm1", "NAThermVaillant"), ("therm2", "NAThermVaillant"))],
        {"h2": {"r2": status(21.0)}},
    )
    assert result == {"therm2": 21.0}


def test_missing_module_type_uses_legacy_fallback():
    """Handle older or mock module objects without a type attribute."""
    result = resolve_room_temperatures(
        [home("h1", room("r1", "therm1"))],
        [Obj(modules=[Obj(id="therm1")])],
        {"h1": {"r1": status(19.5)}},
    )
    assert result == {}
