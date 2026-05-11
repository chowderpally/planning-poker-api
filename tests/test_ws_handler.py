import json

import httpx
import pytest
from httpx_ws import aconnect_ws
from httpx_ws.transport import ASGIWebSocketTransport

from app.main import create_app

app = create_app()


def make_client():
    return httpx.AsyncClient(
        transport=ASGIWebSocketTransport(app=app),
        base_url="http://test",
    )


async def _create_room(client: httpx.AsyncClient) -> str:
    resp = await client.post("/rooms")
    return resp.json()["room_id"]


@pytest.mark.asyncio
async def test_join_and_receive_state():
    async with make_client() as client:
        room_id = await _create_room(client)
        async with aconnect_ws(f"ws://test/ws/{room_id}", client) as ws:
            await ws.send_text(json.dumps({"type": "join", "display_name": "Alice"}))
            msg = json.loads(await ws.receive_text())
    assert msg["type"] == "room_state"
    assert len(msg["players"]) == 1
    assert msg["players"][0]["display_name"] == "Alice"
    assert msg["players"][0]["is_admin"] is True
    assert msg["revealed"] is False


@pytest.mark.asyncio
async def test_vote_hidden_until_reveal():
    async with make_client() as client:
        room_id = await _create_room(client)
        async with aconnect_ws(f"ws://test/ws/{room_id}", client) as ws:
            await ws.send_text(json.dumps({"type": "join", "display_name": "Alice"}))
            await ws.receive_text()  # initial state
            await ws.send_text(json.dumps({"type": "vote", "value": "8"}))
            state = json.loads(await ws.receive_text())
    assert state["players"][0]["has_voted"] is True
    assert state["players"][0]["vote"] is None  # hidden
    assert state["revealed"] is False


@pytest.mark.asyncio
async def test_reveal_shows_votes():
    async with make_client() as client:
        room_id = await _create_room(client)
        async with aconnect_ws(f"ws://test/ws/{room_id}", client) as ws:
            await ws.send_text(json.dumps({"type": "join", "display_name": "Alice"}))
            await ws.receive_text()
            await ws.send_text(json.dumps({"type": "vote", "value": "8"}))
            await ws.receive_text()
            await ws.send_text(json.dumps({"type": "reveal"}))
            state = json.loads(await ws.receive_text())
    assert state["revealed"] is True
    assert state["players"][0]["vote"] == "8"
    assert state["average"] == 8.0


@pytest.mark.asyncio
async def test_reset_clears_votes():
    async with make_client() as client:
        room_id = await _create_room(client)
        async with aconnect_ws(f"ws://test/ws/{room_id}", client) as ws:
            await ws.send_text(json.dumps({"type": "join", "display_name": "Alice"}))
            await ws.receive_text()
            await ws.send_text(json.dumps({"type": "vote", "value": "5"}))
            await ws.receive_text()
            await ws.send_text(json.dumps({"type": "reveal"}))
            await ws.receive_text()
            await ws.send_text(json.dumps({"type": "reset"}))
            state = json.loads(await ws.receive_text())
    assert state["revealed"] is False
    assert state["players"][0]["has_voted"] is False
    assert state["players"][0]["vote"] is None


@pytest.mark.asyncio
async def test_invalid_vote_returns_error():
    async with make_client() as client:
        room_id = await _create_room(client)
        async with aconnect_ws(f"ws://test/ws/{room_id}", client) as ws:
            await ws.send_text(json.dumps({"type": "join", "display_name": "Alice"}))
            await ws.receive_text()
            await ws.send_text(json.dumps({"type": "vote", "value": "999"}))
            msg = json.loads(await ws.receive_text())
    assert msg["type"] == "error"
    assert msg["code"] == "INVALID_VOTE"
