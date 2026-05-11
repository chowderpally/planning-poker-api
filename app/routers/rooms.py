from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.store import create_room, get_room

router = APIRouter(prefix="/rooms", tags=["rooms"])


class CreateRoomResponse(BaseModel):
    room_id: str


@router.post("", response_model=CreateRoomResponse, status_code=201)
async def create_room_endpoint() -> CreateRoomResponse:
    room = await create_room()
    return CreateRoomResponse(room_id=room.room_id)


@router.get("/{room_id}")
async def get_room_endpoint(room_id: str) -> dict:
    room = await get_room(room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return {
        "room_id": room.room_id,
        "story": room.story,
        "player_count": len(room.players),
    }
