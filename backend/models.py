from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship

from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    leagues_created = relationship("League", back_populates="creator")
    memberships = relationship("Membership", back_populates="user", cascade="all, delete-orphan")
    squads = relationship("Squad", back_populates="user", cascade="all, delete-orphan")
    lineups = relationship("Lineup", back_populates="user", cascade="all, delete-orphan")


class League(Base):
    __tablename__ = "leagues"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    creator = relationship("User", back_populates="leagues_created")
    memberships = relationship("Membership", back_populates="league", cascade="all, delete-orphan")
    squads = relationship("Squad", back_populates="league", cascade="all, delete-orphan")
    lineups = relationship("Lineup", back_populates="league", cascade="all, delete-orphan")


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("user_id", "league_id", name="uq_membership_user_league"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)

    user = relationship("User", back_populates="memberships")
    league = relationship("League", back_populates="memberships")


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    position = Column(String, nullable=False)
    team = Column(String, nullable=False)
    cost = Column(Numeric(10, 2), nullable=False)

    squad_entries = relationship(
        "SquadPlayer", back_populates="player", cascade="all, delete-orphan", overlaps="squads"
    )
    squads = relationship(
        "Squad",
        secondary="squad_players",
        back_populates="players",
        overlaps="squad_entries,squad_players",
    )


class Squad(Base):
    __tablename__ = "squads"
    __table_args__ = (UniqueConstraint("user_id", "league_id", name="uq_squad_user_league"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    budget_used = Column(Numeric(10, 2), nullable=False, default=0)

    user = relationship("User", back_populates="squads")
    league = relationship("League", back_populates="squads")
    players = relationship(
        "Player",
        secondary="squad_players",
        back_populates="squads",
        overlaps="squad_entries,squad_players",
    )
    squad_players = relationship(
        "SquadPlayer",
        back_populates="squad",
        cascade="all, delete-orphan",
        overlaps="players,squads",
    )


class SquadPlayer(Base):
    __tablename__ = "squad_players"
    __table_args__ = (UniqueConstraint("squad_id", "player_id", name="uq_squad_player"),)

    id = Column(Integer, primary_key=True)
    squad_id = Column(Integer, ForeignKey("squads.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)

    squad = relationship("Squad", back_populates="squad_players", overlaps="players,squads")
    player = relationship("Player", back_populates="squad_entries", overlaps="players,squads,squad_players")


class Lineup(Base):
    __tablename__ = "lineups"
    __table_args__ = (UniqueConstraint("user_id", "league_id", "gw", name="uq_lineup_user_league_gw"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    gw = Column(Integer, nullable=False)
    captain_player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    vice_captain_player_id = Column(Integer, ForeignKey("players.id"), nullable=False)

    user = relationship("User", back_populates="lineups")
    league = relationship("League", back_populates="lineups")
    slots = relationship("LineupSlot", back_populates="lineup", cascade="all, delete-orphan")


class LineupSlot(Base):
    __tablename__ = "lineup_slots"
    __table_args__ = (UniqueConstraint("lineup_id", "player_id", name="uq_lineup_player"),)

    id = Column(Integer, primary_key=True)
    lineup_id = Column(Integer, ForeignKey("lineups.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    starter = Column(Boolean, nullable=False, default=True)

    lineup = relationship("Lineup", back_populates="slots")
