"""Live match action endpoints: clock control, event save/delete, and substitutions."""
import time
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models import Event, Match, MatchPlayer, Player, Substitution
from utils.match_utils import (
    _PLAYER_STAT_BY_TYPE,
    _PLAYER_STAT_BY_TYPE_AND_RESULT,
    calculate_minute,
    get_active_players,
    get_recent_events,
)

router = APIRouter(prefix="/live")
templates = Jinja2Templates(directory="templates")

SCORE_DELTA = {
    "try": {"any": 5},
    "conversion": {"scored": 2},
    "drop": {"scored": 3},
    "penal": {"kicked": 3},
}

VALID_ACTIONS = {
    "tackle", "try", "conversion", "drop", "scrum", "lineout",
    "ruck", "maul", "penal", "kick", "perdida", "salida", "tarjeta",
}


# ── Clock ──────────────────────────────────────────────────────────────────

@router.post("/{match_id}/clock/start", response_class=HTMLResponse)
async def clock_start(request: Request, match_id: str, db: Session = Depends(get_db)):
    match = _get_match(match_id, db)
    if match.start_timestamp is None:
        match.start_timestamp = int(time.time() * 1000)
        match.status = "live"
        db.commit()
    return _clock_response(request, match)


@router.post("/{match_id}/clock/pause", response_class=HTMLResponse)
async def clock_pause(request: Request, match_id: str, db: Session = Depends(get_db)):
    match = _get_match(match_id, db)
    if match.start_timestamp is not None:
        elapsed = int(time.time() * 1000) - int(match.start_timestamp)
        match.accumulated_time += elapsed
        match.start_timestamp = None
        match.status = "paused"
        db.commit()
    return _clock_response(request, match)


@router.post("/{match_id}/clock/next-period", response_class=HTMLResponse)
async def clock_next_period(request: Request, match_id: str, db: Session = Depends(get_db)):
    match = _get_match(match_id, db)
    if match.period == 1:
        match.period = 2
        match.accumulated_time = 0
        match.start_timestamp = None
        match.status = "paused"
        db.commit()
    return _clock_response(request, match)


# ── Action sheet loader ────────────────────────────────────────────────────

@router.get("/{match_id}/actions/{action_type}", response_class=HTMLResponse)
async def load_action_sheet(
    request: Request,
    match_id: str,
    action_type: str,
    db: Session = Depends(get_db),
):
    if action_type not in VALID_ACTIONS:
        raise HTTPException(status_code=404, detail="Unknown action")
    match = _get_match(match_id, db)
    players = get_active_players(match_id, db)
    return templates.TemplateResponse(f"live/sheets/{action_type}.html", {
        "request": request,
        "match_id": match_id,
        "match": match,
        "players": players,
    })


# ── Event save ─────────────────────────────────────────────────────────────

@router.post("/{match_id}/events", response_class=HTMLResponse)
async def save_event(request: Request, match_id: str, db: Session = Depends(get_db)):
    match = _get_match(match_id, db)
    form = await request.form()

    event_type = form.get("type", "")
    result = form.get("result", "")
    zone_raw = form.get("zone")
    player_id = form.get("player_id") or None
    notes = form.get("notes") or None
    team = form.get("team", "own")
    if team not in ("own", "rival"):
        team = "own"

    event = Event(
        match_id=match_id,
        minute=calculate_minute(match),
        period=match.period,
        team=team,
        type=event_type,
        result=result,
        zone=int(zone_raw) if zone_raw else None,
        player_id=player_id,
        notes=notes,
    )
    db.add(event)

    # Score updates
    deltas = SCORE_DELTA.get(event_type, {})
    delta = deltas.get(result, deltas.get("any", 0))
    if team == "own":
        match.score_own += delta
    else:
        match.score_rival += delta

    # Player stat updates — only for own team
    if team == "own" and player_id:
        player = db.query(Player).filter_by(id=player_id).first()
        if player:
            _update_player_stats(player, event_type, result)

    # Inline conversion when try is saved in the same form
    if event_type == "try" and form.get("conversion_attempted") == "yes":
        conv_result = form.get("conversion_result", "missed")
        conv_player_id = form.get("conversion_player_id") or None
        conv_event = Event(
            match_id=match_id,
            minute=calculate_minute(match),
            period=match.period,
            team=team,
            type="conversion",
            result=conv_result,
            player_id=conv_player_id,
        )
        db.add(conv_event)
        if conv_result == "scored":
            if team == "own":
                match.score_own += 2
            else:
                match.score_rival += 2
        if team == "own" and conv_player_id:
            conv_player = db.query(Player).filter_by(id=conv_player_id).first()
            if conv_player:
                _update_player_stats(conv_player, "conversion", conv_result)

    db.commit()
    db.refresh(match)

    events = get_recent_events(match_id, db)
    return templates.TemplateResponse("live/partials/events_feed.html", {
        "request": request,
        "match": match,
        "events": events,
    })


# ── Substitution ───────────────────────────────────────────────────────────

@router.get("/{match_id}/substitutions/sheet", response_class=HTMLResponse)
async def substitution_sheet(
    request: Request,
    match_id: str,
    player_out_id: str,
    db: Session = Depends(get_db),
):
    _get_match(match_id, db)
    mp_out = db.query(MatchPlayer).filter_by(match_id=match_id, player_id=player_out_id).first()
    if not mp_out:
        raise HTTPException(status_code=404, detail="Player not found in this match")
    player_out = db.query(Player).filter_by(id=player_out_id).first()

    bench = (
        db.query(MatchPlayer, Player)
        .join(Player, MatchPlayer.player_id == Player.id)
        .filter(
            MatchPlayer.match_id == match_id,
            MatchPlayer.is_starter == False,
            MatchPlayer.minute_in == -1,
            MatchPlayer.minute_out.is_(None),
        )
        .order_by(MatchPlayer.number)
        .all()
    )

    return templates.TemplateResponse("live/sheets/substitution.html", {
        "request": request,
        "match_id": match_id,
        "player_out": player_out,
        "player_out_mp": mp_out,
        "bench": bench,
    })


@router.post("/{match_id}/substitutions", response_class=HTMLResponse)
async def save_substitution(request: Request, match_id: str, db: Session = Depends(get_db)):
    match = _get_match(match_id, db)
    form = await request.form()
    player_out_id = form.get("player_out_id")
    player_in_id = form.get("player_in_id")
    position = form.get("position", "")

    mp_out = db.query(MatchPlayer).filter_by(match_id=match_id, player_id=player_out_id).first()
    mp_in = db.query(MatchPlayer).filter_by(match_id=match_id, player_id=player_in_id).first()
    if not mp_out or not mp_in:
        raise HTTPException(status_code=404, detail="Player not found in this match")

    minute = calculate_minute(match)

    sub = Substitution(
        match_id=match_id,
        minute=minute,
        player_out_id=player_out_id,
        player_in_id=player_in_id,
        position=position,
    )
    db.add(sub)

    mp_out.minute_out = minute
    mp_in.minute_in = minute
    mp_in.position = position

    db.commit()

    from utils.match_utils import get_active_players
    active = get_active_players(match_id, db)
    starters = [{"mp": mp, "player": p} for mp, p in active]

    bench_rows = (
        db.query(MatchPlayer, Player)
        .join(Player, MatchPlayer.player_id == Player.id)
        .filter(
            MatchPlayer.match_id == match_id,
            MatchPlayer.is_starter == False,
            MatchPlayer.minute_in == -1,
            MatchPlayer.minute_out.is_(None),
        )
        .order_by(MatchPlayer.number)
        .all()
    )
    bench = [{"mp": mp, "player": p} for mp, p in bench_rows]

    return templates.TemplateResponse("live/partials/on_field.html", {
        "request": request,
        "match": match,
        "starters": starters,
        "bench": bench,
    })


# ── Event delete ───────────────────────────────────────────────────────────

@router.delete("/{match_id}/events/{event_id}", response_class=HTMLResponse)
async def delete_event(request: Request, match_id: str, event_id: str, db: Session = Depends(get_db)):
    match = _get_match(match_id, db)
    event = db.query(Event).filter_by(id=event_id, match_id=match_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Revert score
    deltas = SCORE_DELTA.get(event.type, {})
    delta = deltas.get(event.result, deltas.get("any", 0))
    if event.team == "own":
        match.score_own = max(0, match.score_own - delta)
    else:
        match.score_rival = max(0, match.score_rival - delta)

    # Revert player stats (own only)
    if event.team == "own" and event.player_id:
        player = db.query(Player).filter_by(id=event.player_id).first()
        if player:
            _revert_player_stats(player, event.type, event.result)

    db.delete(event)
    db.commit()
    db.refresh(match)

    events = get_recent_events(match_id, db)
    return templates.TemplateResponse("live/partials/events_feed.html", {
        "request": request,
        "match": match,
        "events": events,
    })


# ── Close match ───────────────────────────────────────────────────────────

@router.post("/{match_id}/close")
async def close_match(match_id: str, db: Session = Depends(get_db)):
    match = _get_match(match_id, db)

    if match.start_timestamp is not None:
        elapsed = int(time.time() * 1000) - int(match.start_timestamp)
        match.accumulated_time += elapsed
        match.start_timestamp = None

    match.status = "finished"
    total_minutes = match.accumulated_time // 60000

    all_mp = (
        db.query(MatchPlayer, Player)
        .join(Player, MatchPlayer.player_id == Player.id)
        .filter(MatchPlayer.match_id == match_id)
        .all()
    )
    for mp, player in all_mp:
        if mp.minute_in < 0:
            continue
        minute_out = mp.minute_out if mp.minute_out is not None else total_minutes
        minutes = max(0, minute_out - mp.minute_in)
        player.games_played += 1
        player.minutes_played += minutes

    db.commit()
    return RedirectResponse(url=f"/live/{match_id}/summary", status_code=303)


# ── Helpers ────────────────────────────────────────────────────────────────

def _get_match(match_id: str, db: Session) -> Match:
    match = db.query(Match).filter_by(id=match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match


def _clock_response(request: Request, match: Match) -> HTMLResponse:
    return templates.TemplateResponse("live/partials/clock.html", {
        "request": request,
        "match": match,
    })


def _update_player_stats(player: Player, event_type: str, result: str) -> None:
    """Increment the player's historical stat counters for the given event."""
    for key in _PLAYER_STAT_BY_TYPE.get(event_type, []):
        setattr(player, key, getattr(player, key) + 1)
    for key in _PLAYER_STAT_BY_TYPE_AND_RESULT.get((event_type, result), []):
        setattr(player, key, getattr(player, key) + 1)


def _revert_player_stats(player: Player, event_type: str, result: str) -> None:
    """Decrement the player's historical stat counters when an event is deleted (floor at 0)."""
    for key in _PLAYER_STAT_BY_TYPE.get(event_type, []):
        setattr(player, key, max(0, getattr(player, key) - 1))
    for key in _PLAYER_STAT_BY_TYPE_AND_RESULT.get((event_type, result), []):
        setattr(player, key, max(0, getattr(player, key) - 1))
