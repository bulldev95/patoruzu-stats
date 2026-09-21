import time
from sqlalchemy import text
from sqlalchemy.orm import Session
from models import Event, MatchPlayer, Player


def accumulate_stat(stats: dict, event_type: str, result: str) -> None:
    def inc(key):
        stats[key] = stats.get(key, 0) + 1

    if event_type == "try":
        inc("tries")
    elif event_type == "conversion":
        inc("conversions_attempts")
        if result == "scored":
            inc("conversions_scored")
    elif event_type == "drop":
        inc("drops_attempts")
        if result == "scored":
            inc("drops_scored")
    elif event_type == "penal" and result == "kicked":
        inc("penals_scored")
    elif event_type == "tackle":
        inc("tackles_total")
        if result == "positive":
            inc("tackles_positive")
        else:
            inc("tackles_missed")
    elif event_type == "tarjeta":
        if result == "yellow":
            inc("yellow_cards")
        elif result == "red":
            inc("red_cards")
        elif result == "red_20":
            inc("red_cards_20min")
    elif event_type == "kick":
        inc("kicks")
    elif event_type == "perdida":
        inc("turnovers")
    elif event_type == "scrum":
        inc("scrums")
        if result == "won":
            inc("scrums_won")
    elif event_type == "lineout":
        inc("lineouts")
        if result in ("won", "stolen"):
            inc("lineouts_won")
    elif event_type == "ruck":
        inc("rucks")
        if result == "won":
            inc("rucks_won")
    elif event_type == "maul":
        inc("mauls")
        if result == "won":
            inc("mauls_won")


def calculate_minute(match) -> int:
    total_ms = match.accumulated_time
    if match.start_timestamp is not None:
        total_ms += int(time.time() * 1000) - int(match.start_timestamp)
    return max(0, int(total_ms / 60000))


def get_active_players(match_id: str, db: Session) -> list:
    """Players currently on the field: starters (minute_in=0) + subs who came on (minute_in>=0).
    Bench players have minute_in=-1 until they enter."""
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
    return (
        db.query(Event)
        .filter(Event.match_id == match_id)
        .order_by(text("rowid DESC"))  # SQLite rowid is insertion-ordered
        .limit(limit)
        .all()
    )
