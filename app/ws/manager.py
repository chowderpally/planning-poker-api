from __future__ import annotations

import json

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._rooms: dict[str, dict[str, WebSocket]] = {}

    def connect(self, room_id: str, player_id: str, ws: WebSocket) -> None:
        self._rooms.setdefault(room_id, {})[player_id] = ws

    def disconnect(self, room_id: str, player_id: str) -> None:
        room_conns = self._rooms.get(room_id, {})
        room_conns.pop(player_id, None)
        if not room_conns:
            self._rooms.pop(room_id, None)

    async def broadcast(self, room_id: str, payload: dict) -> None:
        text = json.dumps(payload, ensure_ascii=False)
        dead: list[str] = []
        for pid, ws in list(self._rooms.get(room_id, {}).items()):
            try:
                await ws.send_text(text)
            except Exception:
                dead.append(pid)
        for pid in dead:
            self.disconnect(room_id, pid)

    async def send_to(self, room_id: str, player_id: str, payload: dict) -> None:
        ws = self._rooms.get(room_id, {}).get(player_id)
        if ws:
            await ws.send_text(json.dumps(payload, ensure_ascii=False))


manager = ConnectionManager()
