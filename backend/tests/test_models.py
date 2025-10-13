import os
import sys
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///./test_models.db"

from backend.auth import get_password_hash, verify_password  # noqa: E402
from backend.db import Base  # noqa: E402
from backend.models import League, Membership, Player, Squad, SquadPlayer, User  # noqa: E402


def setup_module(module):
    engine = create_engine(os.environ["DATABASE_URL"], connect_args={"check_same_thread": False})
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_password_hash_roundtrip():
    password = "secret123"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong", hashed)


def test_relationships():
    engine = create_engine(os.environ["DATABASE_URL"], connect_args={"check_same_thread": False})
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = Session(bind=engine)
    try:
        user = User(name="Test", email="test@example.com", password_hash="hash")
        league = League(name="League", created_by_user_id=1)
        user.leagues_created.append(league)
        session.add(user)
        session.flush()
        membership = Membership(user_id=user.id, league_id=league.id)
        session.add(membership)
        player = Player(name="Player", position="QB", team="X", cost=Decimal("5.0"))
        session.add(player)
        session.flush()
        squad = Squad(user_id=user.id, league_id=league.id, budget_used=Decimal("5.0"))
        session.add(squad)
        session.flush()
        squad_player = SquadPlayer(squad_id=squad.id, player_id=player.id)
        session.add(squad_player)
        session.commit()

        assert squad in user.squads
        assert player in squad.players
        assert membership in user.memberships
    finally:
        session.close()
