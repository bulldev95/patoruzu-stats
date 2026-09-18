import time
from sqlalchemy import text
from sqlalchemy.orm import Session
from models import Event, MatchPlayer, Player


def calculate_minute(match) -> int:
    total_ms = match.accumulated_time
    if match.start_timestamp is not None:
        total_ms += int(time.time() * 1000) - int(match.start_timestamp)
    return max(0, int(total_ms / 60000))


def get_active_players(match_id: str, db: Session) -> list:
    """Players currently on the field (starters not yet replaced).
    Step 9 will extend this to include subs who have come on."""
    return (
        db.query(MatchPlayer, Player)
        .join(Player, MatchPlayer.player_id == Player.id)
        .filter(
            MatchPlayer.match_id == match_id,
            MatchPlayer.is_starter == True,
            MatchPlayer.minute_out.is_(None),
        )
        .order_by(MatchPlayer.number)
        .all()
    )


def get_recent_events(match_id: str, db: Session, limit: int = 10) -> list:
    return (
        db.query(Event)
        .filter(Event.match_id == match_id)
        .order_by(text("rowid DESC"))  # SQLite rowid is insertion-ordered
        .limit(limit)
        .all()
    )
