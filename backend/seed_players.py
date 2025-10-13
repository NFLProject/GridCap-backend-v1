from decimal import Decimal
from typing import List, Tuple

from sqlalchemy.orm import Session

from .models import Player


PLAYERS: List[Tuple[str, str, str, Decimal]] = [
    ("Patrick Mahomes", "QB", "KC", Decimal("12.0")),
    ("Josh Allen", "QB", "BUF", Decimal("11.5")),
    ("Jalen Hurts", "QB", "PHI", Decimal("11.0")),
    ("Justin Herbert", "QB", "LAC", Decimal("10.0")),
    ("Lamar Jackson", "QB", "BAL", Decimal("10.5")),
    ("Christian McCaffrey", "RB", "SF", Decimal("9.5")),
    ("Derrick Henry", "RB", "TEN", Decimal("9.0")),
    ("Austin Ekeler", "RB", "LAC", Decimal("8.5")),
    ("Saquon Barkley", "RB", "NYG", Decimal("9.0")),
    ("Bijan Robinson", "RB", "ATL", Decimal("8.0")),
    ("Nick Chubb", "RB", "CLE", Decimal("8.5")),
    ("Justin Jefferson", "WR", "MIN", Decimal("10.0")),
    ("Ja'Marr Chase", "WR", "CIN", Decimal("9.8")),
    ("Tyreek Hill", "WR", "MIA", Decimal("9.6")),
    ("Stefon Diggs", "WR", "BUF", Decimal("9.0")),
    ("A.J. Brown", "WR", "PHI", Decimal("8.8")),
    ("CeeDee Lamb", "WR", "DAL", Decimal("8.5")),
    ("Davante Adams", "WR", "LV", Decimal("8.4")),
    ("Cooper Kupp", "WR", "LAR", Decimal("9.2")),
    ("Amon-Ra St. Brown", "WR", "DET", Decimal("8.3")),
    ("Travis Kelce", "TE", "KC", Decimal("9.5")),
    ("Mark Andrews", "TE", "BAL", Decimal("7.0")),
    ("T.J. Hockenson", "TE", "MIN", Decimal("6.5")),
    ("George Kittle", "TE", "SF", Decimal("6.8")),
    ("Evan Engram", "TE", "JAX", Decimal("5.5")),
    ("Justin Tucker", "K", "BAL", Decimal("5.0")),
    ("Evan McPherson", "K", "CIN", Decimal("4.5")),
    ("Harrison Butker", "K", "KC", Decimal("4.8")),
    ("Younghoe Koo", "K", "ATL", Decimal("4.2")),
    ("49ers DST", "DST", "SF", Decimal("6.0")),
    ("Cowboys DST", "DST", "DAL", Decimal("5.8")),
    ("Jets DST", "DST", "NYJ", Decimal("5.5")),
    ("Bills DST", "DST", "BUF", Decimal("5.2")),
]


def seed_players(session: Session) -> None:
    if session.query(Player).count() > 0:
        return
    for name, position, team, cost in PLAYERS:
        player = Player(name=name, position=position, team=team, cost=cost)
        session.add(player)
    session.commit()
