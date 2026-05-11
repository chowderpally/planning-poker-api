from __future__ import annotations

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.models.room import FIBONACCI_DECK, Player
from app.store import get_room
from app.ws.manager import manager

router = APIRouter()

_ERRORS = {
    "NOT_ADMIN": "Only the admin can perform this action.",
    "INVALID_VOTE": "Vote value is not in the allowed deck.",
    "ROOM_NOT_FOUND": "Room does not exist or has expired.",
    "BAD_MESSAGE": "Unrecognised or malformed message.",
}


async def _error(room_id: str, player_id: str, code: str) -> None:
    await manager.send_to(
        room_id, player_id, {"type": "error", "code": code, "message": _ERRORS[code]}
    )


@router.websocket("/ws/{room_id}")
async def websocket_endpoint(ws: WebSocket, room_id: str) -> None:
    await ws.accept()

    room = await get_room(room_id)
    if room is None:
        await ws.send_text(
            json.dumps(
                {
                    "type": "error",
                    "code": "ROOM_NOT_FOUND",
                    "message": _ERRORS["ROOM_NOT_FOUND"],
                }
            )
        )
        await ws.close()
        return

    try:
        raw = await ws.receive_text()
        msg = json.loads(raw)
        assert msg.get("type") == "join"
        display_name = str(msg.get("display_name", "")).strip()[:40] or "Anonymous"
    except Exception:
        await ws.close()
        return

    is_first = len(room.players) == 0
    player = Player(display_name=display_name, is_admin=is_first)
    room.players.append(player)
    player_id = player.player_id

    manager.connect(room_id, player_id, ws)
    await manager.broadcast(room_id, room.to_state())

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await _error(room_id, player_id, "BAD_MESSAGE")
                continue

            msg_type = msg.get("type")

            if msg_type == "vote":
                value = str(msg.get("value", "")).strip()
                if value not in FIBONACCI_DECK:
                    await _error(room_id, player_id, "INVALID_VOTE")
                    continue
                if room.revealed:
                    continue
                player.vote = value
                await manager.broadcast(room_id, room.to_state())

            elif msg_type == "reveal":
                if not player.is_admin:
                    await _error(room_id, player_id, "NOT_ADMIN")
                    continue
                room.revealed = True
                await manager.broadcast(room_id, room.to_state())

            elif msg_type == "reset":
                if not player.is_admin:
                    await _error(room_id, player_id, "NOT_ADMIN")
                    continue
                room.revealed = False
                for p in room.players:
                    p.vote = None
                await manager.broadcast(room_id, room.to_state())

            elif msg_type == "set_story":
                if not player.is_admin:
                    await _error(room_id, player_id, "NOT_ADMIN")
                    continue
                room.story = str(msg.get("story", ""))[:200]
                await manager.broadcast(room_id, room.to_state())

            else:
                await _error(room_id, player_id, "BAD_MESSAGE")

    except WebSocketDisconnect:
        manager.disconnect(room_id, player_id)
        room.remove_player(player_id)
        if room.players:
            await manager.broadcast(room_id, room.to_state())
