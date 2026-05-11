from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional

FIBONACCI_DECK = ["1", "2", "3", "5", "8", "13", "21", "?", "☕"]


@dataclass
class Player:
    player_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    display_name: str = ""
    is_admin: bool = False
    vote: Optional[str] = None

    @property
    def has_voted(self) -> bool:
        return self.vote is not None


@dataclass
class Room:
    room_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    story: str = ""
    revealed: bool = False
    players: list[Player] = field(default_factory=list)

    def get_player(self, player_id: str) -> Optional[Player]:
        return next((p for p in self.players if p.player_id == player_id), None)

    def remove_player(self, player_id: str) -> None:
        self.players = [p for p in self.players if p.player_id != player_id]
        if self.players and not any(p.is_admin for p in self.players):
            self.players[0].is_admin = True

    def compute_average(self) -> Optional[float]:
        if not self.revealed:
            return None
        numeric = [
            int(p.vote) for p in self.players if p.vote and p.vote not in ("?", "☕")
        ]
        if not numeric:
            return None
        return round(sum(numeric) / len(numeric), 1)

    def to_state(self) -> dict:
        return {
            "type": "room_state",
            "room_id": self.room_id,
            "story": self.story,
            "revealed": self.revealed,
            "players": [
                {
                    "player_id": p.player_id,
                    "display_name": p.display_name,
                    "is_admin": p.is_admin,
                    "has_voted": p.has_voted,
                    "vote": p.vote if self.revealed else None,
                }
                for p in self.players
            ],
            "average": self.compute_average(),
        }
