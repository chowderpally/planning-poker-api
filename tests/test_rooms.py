import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app

app = create_app()


@pytest.mark.asyncio
async def test_create_room():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post("/rooms")
    assert resp.status_code == 201
    data = resp.json()
    assert "room_id" in data
    assert len(data["room_id"]) == 8


@pytest.mark.asyncio
async def test_get_room():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        create_resp = await client.post("/rooms")
        room_id = create_resp.json()["room_id"]
        resp = await client.get(f"/rooms/{room_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["room_id"] == room_id
    assert data["player_count"] == 0


@pytest.mark.asyncio
async def test_get_room_not_found():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/rooms/doesntexist")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
