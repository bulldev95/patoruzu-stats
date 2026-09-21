"""Business logic for live match actions: clock control, events, substitutions, and match close."""
import time

from fastapi import HTTPException
from sqlalchemy.orm import Session

from constants import PLAYER_STAT_BY_TYPE, PLAYER_STAT_BY_TYPE_AND_RESULT, SCORE_DELTA, VALID_ACTIONS
from models import Event, Substitution
from repositories import match_player_repo, match_repo, player_repo
from services.match_utils import get_active_players, get_recent_events
from utils.match_utils import calculate_minute


def start_clock(db: Session, match_id: str):
    """Start the match clock and set status to live on first start. Returns the match."""
    match = match_repo.get_or_404(db, match_id)
    if match.start_timestamp is None:
        match.start_timestamp = int(time.time() * 1000)
        match.status = "live"
        db.commit()
    return match


def pause_clock(db: Session, match_id: str):
    """Pause the clock and accumulate elapsed time. Returns the match."""
    match = match_repo.get_or_404(db, match_id)
    if match.start_timestamp is not None:
        elapsed = int(time.time() * 1000) - int(match.start_timestamp)
        match.accumulated_time += elapsed
        match.start_timestamp = None
        match.status = "paused"
        db.commit()
    return match


def next_period(db: Session, match_id: str):
    """Advance from period 1 to period 2 and reset the clock. Returns the match."""
    match = match_repo.get_or_404(db, match_id)
    if match.period == 1:
        match.period = 2
        match.accumulated_time = 0
        match.start_timestamp = None
        match.status = "paused"
        db.commit()
    return match


def get_action_sheet_data(db: Session, match_id: str, action_type: str) -> dict:
    """Return context dict for an action sheet template.

    Raises 404 for unknown action types.
    """
    if action_type not in VALID_ACTIONS:
        raise HTTPException(status_code=404, detail="Unknown action")
    match = match_repo.get_or_404(db, match_id)
    players = get_active_players(match_id, db)
    return {"match_id": match_id, "match": match, "players": players}


def save_event(db: Session, match_id: str, data: dict) -> tuple:
    """Persist an event, update match score and player stat counters.

    Handles optional inline conversion when a try form includes conversion_attempted=yes.
    Returns (match, recent_events).
    """
    match = match_repo.get_or_404(db, match_id)

    event_type = data.get("type", "")
    result = data.get("result", "")
    zone_raw = data.get("zone")
    player_id = data.get("player_id") or None
    notes = data.get("notes") or None
    team = data.get("team", "own")
    if team not in ("own", "rival"):
        team = "own"

    db.add(Event(
        match_id=match_id,
        minute=calculate_minute(match),
        period=match.period,
        team=team,
        type=event_type,
        result=result,
        zone=int(zone_raw) if zone_raw else None,
        player_id=player_id,
        notes=notes,
    ))

    deltas = SCORE_DELTA.get(event_type, {})
    delta = deltas.get(result, deltas.get("any", 0))
    if team == "own":
        match.score_own += delta
    else:
        match.score_rival += delta

    if team == "own" and player_id:
        player = player_repo.get_by_id(db, player_id)
        if player:
            _apply_player_stats(player, event_type, result, delta=1)

    if event_type == "try" and data.get("conversion_attempted") == "yes":
        conv_result = data.get("conversion_result", "missed")
        conv_player_id = data.get("conversion_player_id") or None
        db.add(Event(
            match_id=match_id,
            minute=calculate_minute(match),
            period=match.period,
            team=team,
            type="conversion",
            result=conv_result,
            player_id=conv_player_id,
        ))
        if conv_result == "scored":
            if team == "own":
                match.score_own += 2
            else:
                match.score_rival += 2
        if team == "own" and conv_player_id:
            conv_player = player_repo.get_by_id(db, conv_player_id)
            if conv_player:
                _apply_player_stats(conv_player, "conversion", conv_result, delta=1)

    db.commit()
    db.refresh(match)
    return match, get_recent_events(match_id, db)


def get_substitution_sheet_data(db: Session, match_id: str, player_out_id: str) -> dict:
    """Return context dict for the substitution sheet template.

    Raises 404 if the player is not in the match.
    """
    match_repo.get_or_404(db, match_id)
    mp_out = match_player_repo.get_by_match_and_player(db, match_id, player_out_id)
    if not mp_out:
        raise HTTPException(status_code=404, detail="Player not found in this match")
    return {
        "match_id": match_id,
        "player_out": player_repo.get_by_id(db, player_out_id),
        "player_out_mp": mp_out,
        "bench": match_player_repo.get_bench(db, match_id),
    }


def save_substitution(db: Session, match_id: str, data: dict) -> tuple:
    """Record a substitution and update MatchPlayer minute_in/minute_out fields.

    Raises 404 if either player is not found in the match.
    Returns (match, starters, bench).
    """
    match = match_repo.get_or_404(db, match_id)
    player_out_id = data.get("player_out_id")
    player_in_id = data.get("player_in_id")
    position = data.get("position", "")

    mp_out = match_player_repo.get_by_match_and_player(db, match_id, player_out_id)
    mp_in = match_player_repo.get_by_match_and_player(db, match_id, player_in_id)
    if not mp_out or not mp_in:
        raise HTTPException(status_code=404, detail="Player not found in this match")

    minute = calculate_minute(match)
    db.add(Substitution(
        match_id=match_id,
        minute=minute,
        player_out_id=player_out_id,
        player_in_id=player_in_id,
        position=position,
    ))
    mp_out.minute_out = minute
    mp_in.minute_in = minute
    mp_in.position = position
    db.commit()

    starters = [{"mp": mp, "player": p} for mp, p in get_active_players(match_id, db)]
    bench = [{"mp": mp, "player": p} for mp, p in match_player_repo.get_bench(db, match_id)]
    return match, starters, bench


def delete_event(db: Session, match_id: str, event_id: str) -> tuple:
    """Delete an event and revert its score and player stat contributions.

    Returns (match, recent_events).
    """
    match = match_repo.get_or_404(db, match_id)
    event = db.query(Event).filter_by(id=event_id, match_id=match_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    deltas = SCORE_DELTA.get(event.type, {})
    delta = deltas.get(event.result, deltas.get("any", 0))
    if event.team == "own":
        match.score_own = max(0, match.score_own - delta)
    else:
        match.score_rival = max(0, match.score_rival - delta)

    if event.team == "own" and event.player_id:
        player = player_repo.get_by_id(db, event.player_id)
        if player:
            _apply_player_stats(player, event.type, event.result, delta=-1)

    db.delete(event)
    db.commit()
    db.refresh(match)
    return match, get_recent_events(match_id, db)


def close_match(db: Session, match_id: str) -> str:
    """Finalize a match: stop the clock, set status to finished, and tally player minutes.

    Returns match_id for use in the redirect.
    """
    match = match_repo.get_or_404(db, match_id)

    if match.start_timestamp is not None:
        elapsed = int(time.time() * 1000) - int(match.start_timestamp)
        match.accumulated_time += elapsed
        match.start_timestamp = None

    match.status = "finished"
    total_minutes = match.accumulated_time // 60000

    for mp, player in match_player_repo.get_all_with_players(db, match_id):
        if mp.minute_in < 0:
            continue
        minute_out = mp.minute_out if mp.minute_out is not None else total_minutes
        player.games_played += 1
        player.minutes_played += max(0, minute_out - mp.minute_in)

    db.commit()
    return match_id


# ── Private helpers ────────────────────────────────────────────────────────

def _apply_player_stats(player, event_type: str, result: str, delta: int) -> None:
    """Increment or decrement a player's stat counters by delta (+1 to add, -1 to revert).

    Stats are floored at 0 to avoid negative values on revert.
    """
    for key in PLAYER_STAT_BY_TYPE.get(event_type, []):
        setattr(player, key, max(0, getattr(player, key) + delta))
    for key in PLAYER_STAT_BY_TYPE_AND_RESULT.get((event_type, result), []):
        setattr(player, key, max(0, getattr(player, key) + delta))
