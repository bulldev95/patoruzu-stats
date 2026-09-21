"""Live match action endpoints: clock control, event save/delete, and substitutions."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models import Match
from services import actions_service

router = APIRouter(prefix="/live")
templates = Jinja2Templates(directory="templates")


# ── Clock ──────────────────────────────────────────────────────────────────

@router.post("/{match_id}/clock/start", response_class=HTMLResponse)
async def clock_start(request: Request, match_id: str, db: Session = Depends(get_db)):
    """Start the match clock."""
    match = actions_service.start_clock(db, match_id)
    return _clock_response(request, match)


@router.post("/{match_id}/clock/pause", response_class=HTMLResponse)
async def clock_pause(request: Request, match_id: str, db: Session = Depends(get_db)):
    """Pause the match clock."""
    match = actions_service.pause_clock(db, match_id)
    return _clock_response(request, match)


@router.post("/{match_id}/clock/next-period", response_class=HTMLResponse)
async def clock_next_period(request: Request, match_id: str, db: Session = Depends(get_db)):
    """Advance to the second period and reset the clock."""
    match = actions_service.next_period(db, match_id)
    return _clock_response(request, match)


# ── Action sheet loader ────────────────────────────────────────────────────

@router.get("/{match_id}/actions/{action_type}", response_class=HTMLResponse)
async def load_action_sheet(
    request: Request,
    match_id: str,
    action_type: str,
    db: Session = Depends(get_db),
):
    """Render the action input sheet for a given action type."""
    data = actions_service.get_action_sheet_data(db, match_id, action_type)
    return templates.TemplateResponse(f"live/sheets/{action_type}.html", {"request": request, **data})


# ── Event save ─────────────────────────────────────────────────────────────

@router.post("/{match_id}/events", response_class=HTMLResponse)
async def save_event(request: Request, match_id: str, db: Session = Depends(get_db)):
    """Persist an event and return the updated events feed partial."""
    form = await request.form()
    match, events = actions_service.save_event(db, match_id, dict(form))
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
    """Render the substitution selection sheet for a player coming off."""
    data = actions_service.get_substitution_sheet_data(db, match_id, player_out_id)
    return templates.TemplateResponse("live/sheets/substitution.html", {"request": request, **data})


@router.post("/{match_id}/substitutions", response_class=HTMLResponse)
async def save_substitution(request: Request, match_id: str, db: Session = Depends(get_db)):
    """Record a substitution and return the updated on-field roster partial."""
    form = await request.form()
    match, starters, bench = actions_service.save_substitution(db, match_id, dict(form))
    return templates.TemplateResponse("live/partials/on_field.html", {
        "request": request,
        "match": match,
        "starters": starters,
        "bench": bench,
    })


# ── Event delete ───────────────────────────────────────────────────────────

@router.delete("/{match_id}/events/{event_id}", response_class=HTMLResponse)
async def delete_event(request: Request, match_id: str, event_id: str, db: Session = Depends(get_db)):
    """Delete an event, revert its score and stats, and return the updated events feed."""
    match, events = actions_service.delete_event(db, match_id, event_id)
    return templates.TemplateResponse("live/partials/events_feed.html", {
        "request": request,
        "match": match,
        "events": events,
    })


# ── Close match ────────────────────────────────────────────────────────────

@router.post("/{match_id}/close")
async def close_match(match_id: str, db: Session = Depends(get_db)):
    """Finalize the match and redirect to the summary view."""
    match_id = actions_service.close_match(db, match_id)
    return RedirectResponse(url=f"/live/{match_id}/summary", status_code=303)


# ── Helpers ────────────────────────────────────────────────────────────────

def _clock_response(request: Request, match: Match) -> HTMLResponse:
    """Render the clock partial for HTMX clock update responses."""
    return templates.TemplateResponse("live/partials/clock.html", {"request": request, "match": match})
