from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, validator


class UserBase(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class AuthResponse(UserBase):
    token: str


class LeagueCreateRequest(BaseModel):
    name: str


class LeagueJoinRequest(BaseModel):
    league_id: int


class LeagueOut(BaseModel):
    league_id: int
    name: str


class PlayerOut(BaseModel):
    id: int
    name: str
    position: str
    team: str
    cost: float

    class Config:
        orm_mode = True


class SquadSaveRequest(BaseModel):
    league_id: int
    player_ids: List[int]


class SquadPlayerOut(PlayerOut):
    pass


class SquadOut(BaseModel):
    squad_id: int
    league_id: int
    budget_used: float
    players: List[SquadPlayerOut]


class SquadResponse(SquadOut):
    pass


class LineupSetRequest(BaseModel):
    league_id: int
    gw: int
    starters: List[int]
    captain: int
    vice: int

    @validator("starters")
    def validate_starters_length(cls, value: List[int]) -> List[int]:
        if len(value) != 9:
            raise ValueError("Lineup must include exactly 9 starters")
        return value

    @validator("captain", "vice")
    def validate_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Player id must be positive")
        return v


class LineupResponse(BaseModel):
    lineup_id: int


class StandingOut(BaseModel):
    team_name: str
    points: int


class MembershipOut(BaseModel):
    membership_id: int


class LeagueCreateResponse(BaseModel):
    league_id: int


class StandingsResponse(BaseModel):
    standings: List[StandingOut]


class MeResponse(UserBase):
    created_at: Optional[datetime] = None
