"""Resolve home-scoped boiler booleans by stable thermostat module IDs."""

import logging

_LOGGER = logging.getLogger(__name__)


def resolve_boiler_statuses(
    homes, devices, statuses_by_home, boiler_statuses_by_home
) -> dict[str, bool]:
    """Scope readings to home topology and known thermostat IDs; fail closed."""
    thermostat_ids = {
        module.id
        for device in devices
        for module in device.modules
        if getattr(module, "type", None) == "NAThermVaillant" and module.id
    }
    owners: dict[str, set[str]] = {}
    for home in homes:
        if not home.id:
            continue
        for room in home.rooms:
            for module_id in room.module_ids:
                if module_id in thermostat_ids:
                    owners.setdefault(module_id, set()).add(home.id)

    result: dict[str, bool] = {}
    for home in homes:
        statuses = statuses_by_home.get(home.id)
        if statuses is None:
            continue
        readings = boiler_statuses_by_home.get(home.id, {})
        for room in home.rooms:
            status = statuses.get(room.id)
            if status is None or status.reachable is False:
                continue
            for module_id in room.module_ids:
                if owners.get(module_id) != {home.id}:
                    continue
                value = readings.get(module_id)
                if type(value) is bool:
                    result[module_id] = value

    if _LOGGER.isEnabledFor(logging.DEBUG):
        index = 0
        for device in devices:
            for module in device.modules:
                if getattr(module, "type", None) != "NAThermVaillant":
                    continue
                current = result.get(module.id)
                legacy = getattr(module, "boiler_status", None)
                _LOGGER.debug(
                    "Vaillant boiler status: thermostat_index=%d source=%s "
                    "homestatus=%s legacy=%s selected=%s",
                    index,
                    "homestatus" if current is not None else "legacy_fallback",
                    current,
                    legacy,
                    current if current is not None else legacy,
                )
                index += 1
    return result
