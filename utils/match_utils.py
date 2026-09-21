"""Pure match utility functions: minute calculation and stat accumulation (no DB access)."""
import time

from constants import (
    PLAYER_STAT_BY_TYPE,
    PLAYER_STAT_BY_TYPE_AND_RESULT,
    TEAM_STAT_BY_TYPE,
    TEAM_STAT_BY_TYPE_AND_RESULT,
)


def accumulate_player_stat(stats: dict, event_type: str, result: str) -> None:
    """Increment player stat counters in `stats` based on event type and result."""
    for key in PLAYER_STAT_BY_TYPE.get(event_type, []):
        stats[key] = stats.get(key, 0) + 1
    for key in PLAYER_STAT_BY_TYPE_AND_RESULT.get((event_type, result), []):
        stats[key] = stats.get(key, 0) + 1


def accumulate_team_stat(stats: dict, event_type: str, result: str) -> None:
    """Increment team stat counters in `stats` (scrum, lineout, ruck, maul) based on event type and result."""
    for key in TEAM_STAT_BY_TYPE.get(event_type, []):
        stats[key] = stats.get(key, 0) + 1
    for key in TEAM_STAT_BY_TYPE_AND_RESULT.get((event_type, result), []):
        stats[key] = stats.get(key, 0) + 1


def calculate_minute(match) -> int:
    """Return current match minute based on accumulated time and running clock."""
    total_ms = match.accumulated_time
    if match.start_timestamp is not None:
        total_ms += int(time.time() * 1000) - int(match.start_timestamp)
    return max(0, int(total_ms / 60000))
