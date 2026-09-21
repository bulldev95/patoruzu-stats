"""Shared match utilities: minute calculation, active players, recent events, and stat accumulation."""
import time
from sqlalchemy import text
from sqlalchemy.orm import Session
from models import Event, MatchPlayer, Player


_PLAYER_STAT_BY_TYPE: dict[str, list[str]] = {
    "try":        ["tries"],
    "conversion": ["conversions_attempts"],
    "drop":       ["drops_attempts"],
    "tackle":     ["tackles_total"],
    "kick":       ["kicks"],
    "perdida":    ["turnovers"],
}

_PLAYER_STAT_BY_TYPE_AND_RESULT: dict[tuple[str, str], list[str]] = {
    ("conversion", "scored"):   ["conversions_scored"],
    ("drop",       "scored"):   ["drops_scored"],
    ("penal",      "kicked"):   ["penals_scored"],
    ("tackle",     "positive"): ["tackles_positive"],
    ("tackle",     "missed"):   ["tackles_missed"],
    ("tarjeta",    "yellow"):   ["yellow_cards"],
    ("tarjeta",    "red"):      ["red_cards"],
    ("tarjeta",    "red_20"):   ["red_cards_20min"],
}

_TEAM_STAT_BY_TYPE: dict[str, list[str]] = {
    "scrum":   ["scrums"],
    "lineout": ["lineouts"],
    "ruck":    ["rucks"],
    "maul":    ["mauls"],
}

_TEAM_STAT_BY_TYPE_AND_RESULT: dict[tuple[str, str], list[str]] = {
    ("scrum",    "won"):    ["scrums_won"],
    ("lineout",  "won"):    ["lineouts_won"],
    ("lineout",  "stolen"): ["lineouts_won"],
    ("ruck",     "won"):    ["rucks_won"],
    ("maul",     "won"):    ["mauls_won"],
}


def accumulate_player_stat(stats: dict, event_type: str, result: str) -> None:
    """Increment player stats in `stats` dict based on event type and result."""
    for key in _PLAYER_STAT_BY_TYPE.get(event_type, []):
        stats[key] = stats.get(key, 0) + 1
    for key in _PLAYER_STAT_BY_TYPE_AND_RESULT.get((event_type, result), []):
        stats[key] = stats.get(key, 0) + 1


def accumulate_team_stat(stats: dict, event_type: str, result: str) -> None:
    """Increment team stats in `stats` dict (scrum, lineout, ruck, maul) based on event type and result."""
    for key in _TEAM_STAT_BY_TYPE.get(event_type, []):
        stats[key] = stats.get(key, 0) + 1
    for key in _TEAM_STAT_BY_TYPE_AND_RESULT.get((event_type, result), []):
        stats[key] = stats.get(key, 0) + 1


def calculate_minute(match) -> int:
    """Return current match minute based on accumulated time and running clock."""
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
    """Return the most recent events for a match, ordered newest first."""
    return (
        db.query(Event)
        .filter(Event.match_id == match_id)
        .order_by(text("rowid DESC"))  # SQLite rowid is insertion-ordered
        .limit(limit)
        .all()
    )
