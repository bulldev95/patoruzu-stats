import time
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models import Event, Match, Player
from utils.match_utils import calculate_minute, get_active_players, get_recent_events

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
    if event_type == "try":
        player.tries += 1
    elif event_type == "conversion":
        player.conversions_attempts += 1
        if result == "scored":
            player.conversions_scored += 1
    elif event_type == "drop":
        player.drops_attempts += 1
        if result == "scored":
            player.drops_scored += 1
    elif event_type == "penal" and result == "kicked":
        player.penals_scored += 1
    elif event_type == "tackle":
        player.tackles_total += 1
        if result == "positive":
            player.tackles_positive += 1
        else:
            player.tackles_missed += 1
    elif event_type == "tarjeta":
        if result == "yellow":
            player.yellow_cards += 1
        elif result == "red":
            player.red_cards += 1
        elif result == "red_20":
            player.red_cards_20min += 1
    elif event_type == "kick":
        player.kicks += 1
    elif event_type == "perdida":
        player.turnovers += 1
    elif event_type == "lineout" and result in ("won", "stolen"):
        player.lineouts += 1


def _revert_player_stats(player: Player, event_type: str, result: str) -> None:
    if event_type == "try":
        player.tries = max(0, player.tries - 1)
    elif event_type == "conversion":
        player.conversions_attempts = max(0, player.conversions_attempts - 1)
        if result == "scored":
            player.conversions_scored = max(0, player.conversions_scored - 1)
    elif event_type == "drop":
        player.drops_attempts = max(0, player.drops_attempts - 1)
        if result == "scored":
            player.drops_scored = max(0, player.drops_scored - 1)
    elif event_type == "penal" and result == "kicked":
        player.penals_scored = max(0, player.penals_scored - 1)
    elif event_type == "tackle":
        player.tackles_total = max(0, player.tackles_total - 1)
        if result == "positive":
            player.tackles_positive = max(0, player.tackles_positive - 1)
        else:
            player.tackles_missed = max(0, player.tackles_missed - 1)
    elif event_type == "tarjeta":
        if result == "yellow":
            player.yellow_cards = max(0, player.yellow_cards - 1)
        elif result == "red":
            player.red_cards = max(0, player.red_cards - 1)
        elif result == "red_20":
            player.red_cards_20min = max(0, player.red_cards_20min - 1)
    elif event_type == "kick":
        player.kicks = max(0, player.kicks - 1)
    elif event_type == "perdida":
        player.turnovers = max(0, player.turnovers - 1)
    elif event_type == "lineout" and result in ("won", "stolen"):
        player.lineouts = max(0, player.lineouts - 1)
