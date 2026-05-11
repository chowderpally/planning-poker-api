from __future__ import annotations

import asyncio

from app.models.room import Room

_rooms: dict[str, Room] = {}
_lock = asyncio.Lock()


async def create_room() -> Room:
    async with _lock:
        room = Room()
        _rooms[room.room_id] = room
        return room


async def get_room(room_id: str) -> Room | None:
    return _rooms.get(room_id)
