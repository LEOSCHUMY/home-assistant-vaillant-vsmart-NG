"""Map Vaillant home status readings to thermostat modules by stable IDs.

The mappings come from homesdata rooms[].module_ids. Never rely on room order
or assume that a home contains only one thermostat or one room.
"""

from __future__ import annotations


def resolve_room_temperatures(homes, devices, statuses_by_home) -> dict[str, float]:
    """Map thermostat module IDs to unambiguous, reachable room temperatures.

    statuses_by_home is indexed by home ID; each value is the parsed mapping
    returned by ThermostatClient.async_get_home_status().
    """
    thermostat_ids = {
        module.id
        for device in devices
        for module in device.modules
        if module.type == "NAThermVaillant" and module.id
    }
    temperatures: dict[str, float] = {}
    ambiguous: set[str] = set()

    for home in homes:
        statuses = statuses_by_home.get(home.id, {})
        for room in home.rooms:
            if not room.id:
                continue
            status = statuses.get(room.id)
            if status is None or status.reachable is False:
                continue
            temperature = status.measured_temperature
            if temperature is None:
                continue

            for module_id in room.module_ids:
                if module_id not in thermostat_ids or module_id in ambiguous:
                    continue
                if (
                    module_id in temperatures
                    and temperatures[module_id] != temperature
                ):
                    # Conflicting sources: fall back to the legacy endpoint.
                    temperatures.pop(module_id, None)
                    ambiguous.add(module_id)
                else:
                    temperatures[module_id] = temperature

    return temperatures
