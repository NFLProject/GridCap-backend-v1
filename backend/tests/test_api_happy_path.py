import asyncio
import os
import sys
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///./test_api.db"
os.environ["JWT_SECRET"] = "testsecret"

from backend.app import app  # noqa: E402
from backend.db import Base, SessionLocal, engine  # noqa: E402
from backend.seed_players import seed_players  # noqa: E402


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        seed_players(session)
    finally:
        session.close()
    yield
    Base.metadata.drop_all(bind=engine)


async def run_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        register = await client.post(
            "/api/auth/register",
            json={"name": "Alice", "email": "alice@example.com", "password": "password123"},
        )
        assert register.status_code == 200
        token = register.json()["token"]

        login = await client.post(
            "/api/auth/login", json={"email": "alice@example.com", "password": "password123"}
        )
        assert login.status_code == 200
        auth_headers = {"Authorization": f"Bearer {token}"}

        league_resp = await client.post("/api/leagues/create", json={"name": "Alpha"}, headers=auth_headers)
        assert league_resp.status_code == 200
        league_id = league_resp.json()["league_id"]

        join_resp = await client.post("/api/leagues/join", json={"league_id": league_id}, headers=auth_headers)
        assert join_resp.status_code == 400

        my_leagues = await client.get("/api/leagues/mine", headers=auth_headers)
        assert my_leagues.status_code == 200
        assert any(l["league_id"] == league_id for l in my_leagues.json())

        players_resp = await client.get("/api/players", headers=auth_headers)
        assert players_resp.status_code == 200
        players = players_resp.json()
        assert len(players) >= 15
        sorted_players = sorted(players, key=lambda p: p["cost"])
        squad_player_ids = [player["id"] for player in sorted_players[:15]]

        squad_resp = await client.post(
            "/api/squad/save",
            json={"league_id": league_id, "player_ids": squad_player_ids},
            headers=auth_headers,
        )
        assert squad_resp.status_code == 200

        starters = squad_player_ids[:9]
        lineup_resp = await client.post(
            "/api/lineup/set",
            json={
                "league_id": league_id,
                "gw": 1,
                "starters": starters,
                "captain": starters[0],
                "vice": starters[1],
            },
            headers=auth_headers,
        )
        assert lineup_resp.status_code == 200

        standings_resp = await client.get(f"/api/standings/{league_id}", headers=auth_headers)
        assert standings_resp.status_code == 200
        standings = standings_resp.json()["standings"]
        assert isinstance(standings, list)
        assert standings[0]["points"] == 0


def test_happy_path():
    asyncio.run(run_flow())
