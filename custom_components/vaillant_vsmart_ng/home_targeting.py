"""Choose the home and room that receive a command, by stable module IDs.

homesdata rooms[].module_ids place each thermostat in a room of a home.
Accounts can hold several homes and rooms: never rely on their order.
"""

from __future__ import annotations

from collections.abc import Iterable

from vaillant_netatmo_api_ng import Home, Room


def _placements(
    homes: list[Home], module_ids: Iterable[str] | None = None
) -> list[tuple[Home, Room]]:
    """Return each distinct (home, room) pair, or only those listing module_ids.

    The sync API can repeat a room record; repeats count once.
    """
    wanted = None if module_ids is None else set(module_ids)
    placements = {
        (home.id, room.id): (home, room)
        for home in homes
        for room in home.rooms
        if wanted is None or wanted.intersection(room.module_ids)
    }
    return list(placements.values())


def target_home(homes: Iterable[Home], module_ids: Iterable[str]) -> Home | None:
    """Return the one home holding module_ids, or None if that is ambiguous.

    Without topology, an account with a single home is still unambiguous.
    """
    homes = list(homes)
    placed = {home.id: home for home, _ in _placements(homes, module_ids)}
    candidates = list(placed.values()) or homes
    return candidates[0] if len(candidates) == 1 else None


def target_room(homes: Iterable[Home], module_id: str) -> Room | None:
    """Return the one room holding module_id, or None if that is ambiguous.

    Without topology, a single home with a single room is still unambiguous.
    """
    homes = list(homes)
    placements = _placements(homes, [module_id])
    if not placements and len(homes) == 1:
        placements = _placements(homes)
    return placements[0][1] if len(placements) == 1 else None
