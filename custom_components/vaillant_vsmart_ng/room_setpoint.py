"""Map Vaillant homestatus room setpoints to thermostat modules by stable IDs.

homestatus reports a setstate write at once, while getthermostatsdata can still
return the previous mode and target for several seconds. The mappings come
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
