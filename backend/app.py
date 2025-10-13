import os
from decimal import Decimal
from typing import List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import schemas
from .auth import create_access_token, decode_access_token, get_password_hash, verify_password
from .db import Base, SessionLocal, engine, get_db
from .models import League, Lineup, LineupSlot, Membership, Player, Squad, SquadPlayer, User
from .seed_players import seed_players

app = FastAPI(title="GridCap API", openapi_url="/api/openapi.json", docs_url="/api/docs")

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


@app.on_event("startup")
def on_startup() -> None:
    db = SessionLocal()
    try:
        seed_players(db)
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db), authorization: Optional[str] = Header(None)
) -> User:
    if authorization is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    token = authorization.replace("Bearer ", "")
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def serialize_player(player: Player) -> dict:
    return {
        "id": player.id,
        "name": player.name,
        "position": player.position,
        "team": player.team,
        "cost": float(player.cost),
    }


@app.post("/api/auth/register", response_model=schemas.AuthResponse)
def register_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = User(name=payload.name.strip(), email=payload.email.lower(), password_hash=get_password_hash(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": user.id})
    return schemas.AuthResponse(id=user.id, name=user.name, email=user.email, token=token)


@app.post("/api/auth/login", response_model=schemas.AuthResponse)
def login_user(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": user.id})
    return schemas.AuthResponse(id=user.id, name=user.name, email=user.email, token=token)


@app.get("/api/auth/me", response_model=schemas.MeResponse)
def get_me(user: User = Depends(get_current_user)):
    return schemas.MeResponse(id=user.id, name=user.name, email=user.email, created_at=user.created_at)


def ensure_membership(db: Session, user: User, league_id: int) -> League:
    league = db.query(League).filter(League.id == league_id).first()
    if not league:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="League not found")
    membership = db.query(Membership).filter(Membership.user_id == user.id, Membership.league_id == league_id).first()
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this league")
    return league


@app.post("/api/leagues/create", response_model=schemas.LeagueCreateResponse)
def create_league(payload: schemas.LeagueCreateRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    league = League(name=payload.name.strip(), created_by_user_id=user.id)
    db.add(league)
    db.commit()
    db.refresh(league)
    membership = Membership(user_id=user.id, league_id=league.id)
    db.add(membership)
    db.commit()
    return schemas.LeagueCreateResponse(league_id=league.id)


@app.post("/api/leagues/join", response_model=schemas.MembershipOut)
def join_league(payload: schemas.LeagueJoinRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    league = db.query(League).filter(League.id == payload.league_id).first()
    if not league:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="League not found")
    membership = db.query(Membership).filter(Membership.user_id == user.id, Membership.league_id == payload.league_id).first()
    if membership:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already a member")
    membership = Membership(user_id=user.id, league_id=payload.league_id)
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return schemas.MembershipOut(membership_id=membership.id)


@app.get("/api/leagues/mine", response_model=List[schemas.LeagueOut])
def list_my_leagues(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    memberships = (
        db.query(Membership)
        .filter(Membership.user_id == user.id)
        .join(League, Membership.league_id == League.id)
        .all()
    )
    return [schemas.LeagueOut(league_id=m.league.id, name=m.league.name) for m in memberships]


@app.get("/api/players", response_model=List[schemas.PlayerOut])
def list_players(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    players = db.query(Player).order_by(Player.position, Player.cost.desc()).all()
    return [serialize_player(player) for player in players]


@app.post("/api/squad/save", response_model=schemas.SquadResponse)
def save_squad(payload: schemas.SquadSaveRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    league = ensure_membership(db, user, payload.league_id)
    if len(payload.player_ids) != 15:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Squad must have exactly 15 players")
    players = db.query(Player).filter(Player.id.in_(payload.player_ids)).all()
    if len(players) != 15:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid player selection")
    total_cost = sum(Decimal(player.cost) for player in players)
    if total_cost > Decimal("100.0"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Budget exceeded")
    for player in players:
        if player.position not in {"QB", "RB", "WR", "TE", "K", "DST"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid player position")
    squad = db.query(Squad).filter(Squad.user_id == user.id, Squad.league_id == league.id).first()
    if not squad:
        squad = Squad(user_id=user.id, league_id=league.id)
        db.add(squad)
        db.commit()
        db.refresh(squad)
    squad.budget_used = total_cost
    squad.squad_players.clear()
    db.commit()
    for player in players:
        squad_player = SquadPlayer(squad_id=squad.id, player_id=player.id)
        db.add(squad_player)
    db.commit()
    db.refresh(squad)
    return schemas.SquadResponse(
        squad_id=squad.id,
        league_id=league.id,
        budget_used=float(squad.budget_used or 0),
        players=[serialize_player(player) for player in squad.players],
    )


@app.get("/api/squad", response_model=Optional[schemas.SquadResponse])
def get_squad(league_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ensure_membership(db, user, league_id)
    squad = db.query(Squad).filter(Squad.user_id == user.id, Squad.league_id == league_id).first()
    if not squad:
        return None
    return schemas.SquadResponse(
        squad_id=squad.id,
        league_id=league_id,
        budget_used=float(squad.budget_used or 0),
        players=[serialize_player(player) for player in squad.players],
    )


@app.post("/api/lineup/set", response_model=schemas.LineupResponse)
def set_lineup(payload: schemas.LineupSetRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ensure_membership(db, user, payload.league_id)
    squad = db.query(Squad).filter(Squad.user_id == user.id, Squad.league_id == payload.league_id).first()
    if not squad:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Squad not found")
    starter_ids = set(payload.starters)
    if payload.captain not in starter_ids or payload.vice not in starter_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Captain and vice must be starters")
    if payload.captain == payload.vice:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Captain and vice must differ")
    squad_player_ids = {player.id for player in squad.players}
    if not starter_ids.issubset(squad_player_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Starters must be in squad")
    lineup = (
        db.query(Lineup)
        .filter(Lineup.user_id == user.id, Lineup.league_id == payload.league_id, Lineup.gw == payload.gw)
        .first()
    )
    if not lineup:
        lineup = Lineup(
            user_id=user.id,
            league_id=payload.league_id,
            gw=payload.gw,
            captain_player_id=payload.captain,
            vice_captain_player_id=payload.vice,
        )
        db.add(lineup)
        db.commit()
        db.refresh(lineup)
    else:
        lineup.captain_player_id = payload.captain
        lineup.vice_captain_player_id = payload.vice
        lineup.slots.clear()
        db.commit()
    for starter_id in starter_ids:
        slot = LineupSlot(lineup_id=lineup.id, player_id=starter_id, starter=True)
        db.add(slot)
    db.commit()
    db.refresh(lineup)
    return schemas.LineupResponse(lineup_id=lineup.id)


@app.get("/api/standings/{league_id}", response_model=schemas.StandingsResponse)
def get_standings(league_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ensure_membership(db, user, league_id)
    memberships = (
        db.query(Membership)
        .filter(Membership.league_id == league_id)
        .join(User, Membership.user_id == User.id)
        .all()
    )
    standings = [schemas.StandingOut(team_name=m.user.name, points=0) for m in memberships]
    return schemas.StandingsResponse(standings=standings)
