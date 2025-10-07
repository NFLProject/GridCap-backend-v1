import os
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import sessionmaker, declarative_base, Session, relationship

# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./db.sqlite3")

# SQLite needs check_same_thread=False for single-process usage
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    entries = relationship("Entry", back_populates="user")


class League(Base):
    __tablename__ = "leagues"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    entries = relationship("Entry", back_populates="league")


class Entry(Base):
    __tablename__ = "entries"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    team_name = Column(String, nullable=False)
    total_points = Column(Integer, default=0)

    user = relationship("User", back_populates="entries")
    league = relationship("League", back_populates="entries")
    squad = relationship("SquadPlayer", cascade="all, delete-orphan", back_populates="entry")
    lineups = relationship("Lineup", cascade="all, delete-orphan", back_populates="entry")

    __table_args__ = (
        UniqueConstraint("user_id", "league_id", name="uq_entry_user_league"),
    )


class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    position = Column(String, nullable=False)  # QB/RB/WR/TE/K/DST
    team = Column(String, nullable=False)
    cost = Column(Float, nullable=False, default=5.0)

    __table_args__ = (
        UniqueConstraint("name", "team", name="uq_player_name_team"),
    )


class Gameweek(Base):
    __tablename__ = "gameweeks"
    id = Column(Integer, primary_key=True)  # e.g., 1,2,3...
    deadline = Column(DateTime, nullable=False)


class SquadPlayer(Base):
    __tablename__ = "squad_players"
    id = Column(Integer, primary_key=True)
    entry_id = Column(Integer, ForeignKey("entries.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)

    entry = relationship("Entry", back_populates="squad")
    player = relationship("Player")

    __table_args__ = (
        UniqueConstraint("entry_id", "player_id", name="uq_squad_entry_player"),
    )


class Lineup(Base):
    __tablename__ = "lineups"
    id = Column(Integer, primary_key=True)
    entry_id = Column(Integer, ForeignKey("entries.id"), nullable=False)
    gw = Column(Integer, nullable=False, default=1)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    is_starter = Column(Boolean, default=False)
    is_captain = Column(Boolean, default=False)
    is_vice = Column(Boolean, default=False)

    entry = relationship("Entry", back_populates="lineups")
    player = relationship("Player")

    __table_args__ = (
        UniqueConstraint("entry_id", "gw", "player_id", name="uq_lineup_unique"),
    )


Base.metadata.create_all(bind=engine)


# -----------------------------------------------------------------------------
# FastAPI app & CORS
# -----------------------------------------------------------------------------
app = FastAPI(title="NFL Fantasy (FPL-style)", version="0.1.0")

# Allow your Vercel frontend domain(s)
origins = [
    os.getenv("FRONTEND_ORIGIN", "https://nfl-fpl-site.vercel.app"),
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# Dependencies
# -----------------------------------------------------------------------------
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    x_user_id: Optional[int] = Header(default=None, convert_underscores=False),
    db: Session = Depends(get_db)
) -> User:
    """
    Lightweight auth: we accept X-USER-ID header (int)
    to match the current frontend. You can switch to JWT later.
    """
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-USER-ID header")
    user = db.query(User).get(x_user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user")
    return user


# -----------------------------------------------------------------------------
# Pydantic schemas
# -----------------------------------------------------------------------------
class RegisterReq(BaseModel):
    name: str
    email: str


class MeResp(BaseModel):
    id: int
    name: str
    email: str


class LeagueCreateReq(BaseModel):
    name: str
    team_name: str


class LeagueJoinReq(BaseModel):
    league_id: int
    team_name: str


class PlayerOut(BaseModel):
    id: int
    name: str
    position: str
    team: str
    cost: float


class SquadSetReq(BaseModel):
    league_id: int
    player_ids: List[int] = Field(..., description="Exactly 15 player IDs")


class LineupSetReq(BaseModel):
    league_id: int
    starters: List[int] = Field(..., description="Exactly 9 player IDs from your squad")
    captain_id: Optional[int] = None
    vice_id: Optional[int] = None
    chip: Optional[str] = Field(None, description="bench_boost | triple_captain | free_hit | None")


class GameweekCreateReq(BaseModel):
    id: int
    deadline: datetime


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
VALID_POS = {"QB", "RB", "WR", "TE", "K", "DST"}


def ensure_entry(db: Session, user_id: int, league_id: int) -> Entry:
    entry = (
        db.query(Entry)
        .filter(Entry.user_id == user_id, Entry.league_id == league_id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=400, detail="You are not in this league yet.")
    return entry


def group_players_by_position(players: List[Player]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {pos: [] for pos in VALID_POS}
    for p in players:
        grouped[p.position].append(
            {"id": p.id, "name": p.name, "team": p.team, "cost": p.cost}
        )
    return grouped


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"ok": True}


@app.post("/register")
def register(req: RegisterReq, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if user:
        # Return existing (idempotent registration for this MVP)
        return {"user_id": user.id, "name": user.name, "email": user.email}

    user = User(name=req.name, email=req.email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"user_id": user.id, "name": user.name, "email": user.email}


@app.get("/me", response_model=MeResp)
def me(current: User = Depends(get_current_user)):
    return MeResp(id=current.id, name=current.name, email=current.email)


@app.post("/league/create")
def league_create(
    req: LeagueCreateReq,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    league = League(name=req.name, created_by=current.id)
    db.add(league)
    db.commit()
    db.refresh(league)

    entry = Entry(user_id=current.id, league_id=league.id, team_name=req.team_name)
    db.add(entry)
    db.commit()
    db.refresh(entry)

    return {
        "league_id": league.id,
        "league_name": league.name,
        "entry_id": entry.id,
        "team_name": entry.team_name,
    }


@app.post("/league/join")
def league_join(
    req: LeagueJoinReq,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    league = db.query(League).get(req.league_id)
    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    # don't make duplicates
    existing = (
        db.query(Entry)
        .filter(Entry.user_id == current.id, Entry.league_id == req.league_id)
        .first()
    )
    if existing:
        return {
            "entry_id": existing.id,
            "league_id": existing.league_id,
            "team_name": existing.team_name,
            "message": "Already joined",
        }

    entry = Entry(user_id=current.id, league_id=req.league_id, team_name=req.team_name)
    db.add(entry)
    db.commit()
    db.refresh(entry)

    return {
        "entry_id": entry.id,
        "league_id": entry.league_id,
        "team_name": entry.team_name,
    }


@app.get("/players", response_model=List[PlayerOut])
def list_players(db: Session = Depends(get_db)):
    players = db.query(Player).order_by(Player.position, Player.cost.desc()).all()
    return [PlayerOut(id=p.id, name=p.name, position=p.position, team=p.team, cost=p.cost) for p in players]


# ---- optional: seed a decent pool of players --------------------------------
# Call once from /docs after deploy: POST /players/sync
class SeedResp(BaseModel):
    inserted: int
    total: int


@app.post("/players/sync", response_model=SeedResp)
def seed_players(db: Session = Depends(get_db)):
    seed_data = [
        # QBs
        ("Patrick Mahomes", "QB", "KC", 12.5),
        ("Josh Allen", "QB", "BUF", 12.0),
        ("Jalen Hurts", "QB", "PHI", 11.5),
        ("Lamar Jackson", "QB", "BAL", 11.0),
        ("Joe Burrow", "QB", "CIN", 10.5),
        ("Justin Herbert", "QB", "LAC", 10.0),
        ("Tua Tagovailoa", "QB", "MIA", 9.5),
        ("C.J. Stroud", "QB", "HOU", 9.0),
        ("Dak Prescott", "QB", "DAL", 9.0),
        ("Trevor Lawrence", "QB", "JAX", 8.5),

        # RBs
        ("Christian McCaffrey", "RB", "SF", 11.5),
        ("Bijan Robinson", "RB", "ATL", 10.5),
        ("Saquon Barkley", "RB", "PHI", 10.5),
        ("Derrick Henry", "RB", "BAL", 10.0),
        ("Jonathan Taylor", "RB", "IND", 10.0),
        ("Breece Hall", "RB", "NYJ", 9.5),
        ("Josh Jacobs", "RB", "GB", 9.0),
        ("Kyren Williams", "RB", "LAR", 8.5),
        ("Aaron Jones", "RB", "MIN", 8.5),
        ("Jahmyr Gibbs", "RB", "DET", 9.5),
        ("Joe Mixon", "RB", "HOU", 8.5),
        ("Isiah Pacheco", "RB", "KC", 8.0),
        ("Nick Chubb", "RB", "CLE", 9.0),
        ("Kenneth Walker III", "RB", "SEA", 8.0),
        ("Rachaad White", "RB", "TB", 8.0),

        # WRs
        ("Justin Jefferson", "WR", "MIN", 11.5),
        ("Ja'Marr Chase", "WR", "CIN", 11.0),
        ("Tyreek Hill", "WR", "MIA", 11.5),
        ("Amon-Ra St. Brown", "WR", "DET", 10.5),
        ("CeeDee Lamb", "WR", "DAL", 10.5),
        ("A.J. Brown", "WR", "PHI", 10.5),
        ("Garrett Wilson", "WR", "NYJ", 9.0),
        ("Puka Nacua", "WR", "LAR", 9.0),
        ("Davante Adams", "WR", "LV", 9.5),
        ("Stefon Diggs", "WR", "HOU", 9.5),
        ("Mike Evans", "WR", "TB", 8.5),
        ("DJ Moore", "WR", "CHI", 8.5),
        ("Jaylen Waddle", "WR", "MIA", 9.0),
        ("Aiyuk Brandon", "WR", "SF", 8.5),
        ("Deebo Samuel", "WR", "SF", 8.5),
        ("Nico Collins", "WR", "HOU", 8.5),
        ("Keenan Allen", "WR", "CHI", 8.5),
        ("Tee Higgins", "WR", "CIN", 8.0),
        ("DeVonta Smith", "WR", "PHI", 8.5),
        ("Drake London", "WR", "ATL", 8.0),

        # TEs
        ("Travis Kelce", "TE", "KC", 10.0),
        ("Mark Andrews", "TE", "BAL", 9.0),
        ("Sam LaPorta", "TE", "DET", 8.5),
        ("George Kittle", "TE", "SF", 8.5),
        ("T.J. Hockenson", "TE", "MIN", 8.5),
        ("David Njoku", "TE", "CLE", 7.5),
        ("Evan Engram", "TE", "JAX", 7.5),
        ("Kyle Pitts", "TE", "ATL", 7.5),
        ("Dallas Goedert", "TE", "PHI", 7.5),
        ("Dalton Kincaid", "TE", "BUF", 7.5),

        # Ks
        ("Justin Tucker", "K", "BAL", 5.5),
        ("Harrison Butker", "K", "KC", 5.5),
        ("Jake Elliott", "K", "PHI", 5.0),
        ("Tyler Bass", "K", "BUF", 5.0),
        ("Evan McPherson", "K", "CIN", 5.0),
        ("Jason Myers", "K", "SEA", 5.0),

        # DST
        ("49ers DST", "DST", "SF", 5.0),
        ("Cowboys DST", "DST", "DAL", 5.0),
        ("Ravens DST", "DST", "BAL", 5.0),
        ("Chiefs DST", "DST", "KC", 5.0),
        ("Bills DST", "DST", "BUF", 5.0),
        ("Jets DST", "DST", "NYJ", 4.5),
        ("Eagles DST", "DST", "PHI", 4.5),
        ("Steelers DST", "DST", "PIT", 4.5),
        ("Browns DST", "DST", "CLE", 4.5),
        ("Dolphins DST", "DST", "MIA", 4.5),
    ]

    inserted = 0
    for name, pos, team, cost in seed_data:
        if pos not in VALID_POS:
            continue
        exists = db.query(Player).filter(Player.name == name, Player.team == team).first()
        if not exists:
            db.add(Player(name=name, position=pos, team=team, cost=cost))
            inserted += 1
    db.commit()

    total = db.query(Player).count()
    return SeedResp(inserted=inserted, total=total)


@app.get("/squad")
def get_squad(
    league_id: Optional[int] = None,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # If no league_id provided, use the most recent entry for the user
    entry_q = db.query(Entry).filter(Entry.user_id == current.id)
    if league_id:
        entry_q = entry_q.filter(Entry.league_id == league_id)
    entry = entry_q.order_by(Entry.id.desc()).first()
    if not entry:
        return {"entry_id": None, "league_id": league_id, "squad": {}, "message": "No entry yet"}

    players = [sp.player for sp in entry.squad]
    grouped = group_players_by_position(players)
    return {"entry_id": entry.id, "league_id": entry.league_id, "squad": grouped}


@app.post("/squad/set")
def set_squad(
    req: SquadSetReq,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    entry = ensure_entry(db, current.id, req.league_id)

    # Check 15 players exist and positions are valid
    if len(req.player_ids) != 15:
        raise HTTPException(status_code=400, detail="You must select exactly 15 players.")

    players = db.query(Player).filter(Player.id.in__(req.player_ids)).all()
    if len(players) != 15:
        raise HTTPException(status_code=400, detail="Some players not found.")

    # Clear existing squad
    db.query(SquadPlayer).filter(SquadPlayer.entry_id == entry.id).delete()

    # Insert new squad
    for p in players:
        if p.position not in VALID_POS:
            raise HTTPException(status_code=400, detail=f"Invalid position: {p.position}")
        db.add(SquadPlayer(entry_id=entry.id, player_id=p.id))

    db.commit()
    return {"ok": True, "entry_id": entry.id, "league_id": entry.league_id}


@app.post("/lineup/set")
def set_lineup(
    req: LineupSetReq,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    entry = ensure_entry(db, current.id, req.league_id)

    # Very light validation
    if len(req.starters) != 9:
        raise HTTPException(status_code=400, detail="You must set exactly 9 starters.")

    # Ensure starters are from the user's squad
    squad_ids = {sp.player_id for sp in entry.squad}
    if not set(req.starters).issubset(squad_ids):
        raise HTTPException(status_code=400, detail="All starters must be in your squad.")

    # Clear lineup for gw=1 (simple MVP)
    db.query(Lineup).filter(Lineup.entry_id == entry.id, Lineup.gw == 1).delete()

    # Create lineup rows
    for pid in req.starters:
        is_capt = (pid == req.captain_id)
        is_vice = (pid == req.vice_id)
        db.add(Lineup(
            entry_id=entry.id,
            gw=1,
            player_id=pid,
            is_starter=True,
            is_captain=is_capt,
            is_vice=is_vice,
        ))

    db.commit()
    return {"ok": True, "entry_id": entry.id, "league_id": entry.league_id, "chip": req.chip or None}


@app.get("/standings/{league_id}")
def get_standings(
    league_id: int,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entries = db.query(Entry).filter(Entry.league_id == league_id).all()
    rows = [
        {"entry_id": e.id, "team": e.team_name, "points": (e.total_points or 0)}
        for e in entries
    ]
    rows.sort(key=lambda r: r["points"], reverse=True)
    return {"league_id": league_id, "standings": rows}


@app.post("/gameweeks/create")
def create_gw(
    req: GameweekCreateReq,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(Gameweek).get(req.id)
    if existing:
        existing.deadline = req.deadline
        db.add(existing)
    else:
        db.add(Gameweek(id=req.id, deadline=req.deadline))
    db.commit()
    return {"ok": True, "gw": req.id, "deadline": req.deadline.isoformat()}


@app.get("/")
def root():
    return {"message": "NFL FPL-style API is running"}
