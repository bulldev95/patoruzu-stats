import time
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models import Event, Match
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

    event = Event(
        match_id=match_id,
        minute=calculate_minute(match),
        period=match.period,
        team="own",
        type=event_type,
        result=result,
        zone=int(zone_raw) if zone_raw else None,
        player_id=player_id,
        notes=notes,
    )
    db.add(event)

    # Score updates
    deltas = SCORE_DELTA.get(event_type, {})
    match.score_own += deltas.get(result, deltas.get("any", 0))

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
