"""Match service helpers that require database access: active players and recent events."""
from sqlalchemy import text
from sqlalchemy.orm import Session

from models import Event, MatchPlayer, Player


def get_active_players(match_id: str, db: Session) -> list:
    """Return players currently on the field for a match.

    Includes starters (minute_in=0) and subs who entered (minute_in>=0).
    Excludes bench players (minute_in=-1) and players who left (minute_out set).
    """
    return (
        db.query(MatchPlayer, Player)
        .join(Player, MatchPlayer.player_id == Player.id)
        .filter(
            MatchPlayer.match_id == match_id,
            MatchPlayer.minute_out.is_(None),
            MatchPlayer.minute_in >= 0,
        )
        .order_by(MatchPlayer.number)
        .all()
    )


def get_recent_events(match_id: str, db: Session, limit: int = 10) -> list:
    """Return the most recent events for a match, ordered newest first."""
    return (
        db.query(Event)
        .filter(Event.match_id == match_id)
        .order_by(text("rowid DESC"))  # SQLite rowid is insertion-ordered
        .limit(limit)
        .all()
    )
