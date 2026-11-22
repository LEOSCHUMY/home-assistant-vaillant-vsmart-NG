"""Map Vaillant homestatus room setpoints to thermostat modules by stable IDs.

Right after a setstate write, getthermostatsdata can still return the previous
mode and target, while homestatus may already report the new ones. How quickly
either endpoint catches up is up to the cloud and is not guaranteed. The mappings come
from homesdata rooms[].module_ids; never rely on room order.
"""

from __future__ import annotations

from dataclasses import dataclass

# Room therm_setpoint_mode values with a known climate meaning. Anything else
# (away, frost guard, off, ...) is left to the legacy endpoint.
SETPOINT_MODE_SCHEDULE = "home"
SETPOINT_MODE_MANUAL = "manual"
KNOWN_SETPOINT_MODES = (SETPOINT_MODE_SCHEDULE, SETPOINT_MODE_MANUAL)


@dataclass(frozen=True)
class RoomSetpoint:
    """Current setpoint mode and target of the room holding a thermostat."""

    mode: str
    temperature: float | None


def resolve_room_setpoints(homes, devices, statuses_by_home) -> dict[str, RoomSetpoint]:
    """Map thermostat module IDs to unambiguous, reachable room setpoints.

    Only rooms reporting a setpoint mode are used; with a library that does
    not expose it (vaillant-netatmo-api-ng 0.3.0) the result is empty and the
    climate entity keeps reading getthermostatsdata.
    """
    thermostat_ids = {
        module.id
        for device in devices
        for module in device.modules
        if getattr(module, "type", None) == "NAThermVaillant" and module.id
    }
    setpoints: dict[str, RoomSetpoint] = {}
    ambiguous: set[str] = set()

    for home in homes:
        statuses = statuses_by_home.get(home.id, {})
        for room in home.rooms:
            if not room.id:
                continue
            status = statuses.get(room.id)
            if status is None or status.reachable is False:
                continue
            mode = getattr(status, "setpoint_mode", None)
            if not isinstance(mode, str) or not mode:
                continue
            setpoint = RoomSetpoint(mode, status.setpoint_temperature)

            for module_id in room.module_ids:
                if module_id not in thermostat_ids or module_id in ambiguous:
                    continue
                if module_id in setpoints and setpoints[module_id] != setpoint:
                    # Conflicting sources: fall back to the legacy endpoint.
                    setpoints.pop(module_id, None)
                    ambiguous.add(module_id)
                else:
                    setpoints[module_id] = setpoint

    return setpoints


SOURCE_HOMESTATUS = "homestatus"
SOURCE_LEGACY = "getthermostatsdata_fallback"


@dataclass(frozen=True)
class SelectedSetpoint:
    """Mode and target the climate entity shows, each with where it came from.

    mode is SETPOINT_MODE_MANUAL or SETPOINT_MODE_SCHEDULE.
    """

    mode: str
    mode_source: str
    temperature: float | None
    temperature_source: str


def select_climate_setpoint(room_setpoint: RoomSetpoint | None, module) -> SelectedSetpoint:
    """Choose the climate mode and target, field by field.

    The homestatus room is used only for a known mode; its target only when it
    reports one. Everything else comes from the getthermostatsdata module. The
    climate entity and the coordinator's debug log both call this, so the log
    cannot disagree with what the entity shows.
    """
    usable = (
        room_setpoint
        if room_setpoint is not None and room_setpoint.mode in KNOWN_SETPOINT_MODES
        else None
    )

    if usable is not None:
        mode, mode_source = usable.mode, SOURCE_HOMESTATUS
    else:
        mode = (
            SETPOINT_MODE_MANUAL
            if module.setpoint_manual.setpoint_activate
            else SETPOINT_MODE_SCHEDULE
        )
        mode_source = SOURCE_LEGACY

    if usable is not None and usable.temperature is not None:
        temperature, temperature_source = usable.temperature, SOURCE_HOMESTATUS
    else:
        measured = module.measured
        temperature = (
            measured.est_setpoint_temp
            if measured.est_setpoint_temp is not None
            else measured.setpoint_temp
        )
        temperature_source = SOURCE_LEGACY

    return SelectedSetpoint(mode, mode_source, temperature, temperature_source)
