"""Tests for the homestatus-to-thermostat mapping without HA dependencies."""

from types import SimpleNamespace as Obj

from custom_components.vaillant_vsmart.room_temperature import (
    resolve_room_temperatures,
)


def home(home_id, *rooms):
    return Obj(id=home_id, rooms=list(rooms))


def room(room_id, *modules):
    return Obj(id=room_id, module_ids=list(modules))


def device(*modules):
    return Obj(modules=[Obj(id=module_id, type=module_type) for module_id, module_type in modules])


def status(temp, reachable=True):
    return Obj(measured_temperature=temp, reachable=reachable)


def test_one_thermostat_one_room():
    result = resolve_room_temperatures(
        [home("h1", room("r1", "therm1"))],
        [device(("therm1", "NAThermVaillant"))],
        {"h1": {"r1": status(19.5)}},
    )
    assert result == {"therm1": 19.5}


def test_multiple_rooms_map_to_their_own_thermostats():
    result = resolve_room_temperatures(
        [home("h1", room("r1", "therm1"), room("r2", "therm2"))],
        [device(("therm1", "NAThermVaillant"), ("therm2", "NAThermVaillant"))],
        {"h1": {"r1": status(18.5), "r2": status(20.0)}},
    )
    assert result == {"therm1": 18.5, "therm2": 20.0}


def test_missing_unreachable_and_nonthermostat_modules_fall_back():
    result = resolve_room_temperatures(
        [home("h1", room("r1", "therm1"), room("r2", "therm2"), room("r3", "bridge"))],
        [device(("therm1", "NAThermVaillant"),
                ("therm2", "NAThermVaillant"), ("bridge", "NAVaillant"))],
        {"h1": {"r1": status(None), "r2": status(20.0, False), "r3": status(19.0)}},
    )
    assert result == {}


def test_conflicting_mapping_stays_on_fallback_even_after_third_record():
    result = resolve_room_temperatures(
        [home("h1", room("r1", "therm1"), room("r2", "therm1"),
              room("r3", "therm1"))],
        [device(("therm1", "NAThermVaillant"))],
        {"h1": {"r1": status(18.0), "r2": status(19.0), "r3": status(19.0)}},
    )
    assert result == {}


def test_unavailable_home_does_not_block_another_home():
    result = resolve_room_temperatures(
        [home("h1", room("r1", "therm1")), home("h2", room("r2", "therm2"))],
        [device(("therm1", "NAThermVaillant"), ("therm2", "NAThermVaillant"))],
        {"h2": {"r2": status(21.0)}},
    )
    assert result == {"therm2": 21.0}
