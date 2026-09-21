"""Live match view endpoints: match display and post-match summary."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from repositories import match_player_repo, match_repo
from services import stats_service
from services.match_utils import get_active_players, get_recent_events

router = APIRouter(prefix="/live")
templates = Jinja2Templates(directory="templates")


@router.get("/{match_id}", response_class=HTMLResponse)
async def live_view(request: Request, match_id: str, db: Session = Depends(get_db)):
    """Render the live match view with current roster, bench, and recent events."""
    match = match_repo.get_or_404(db, match_id)
    starters = [{"mp": mp, "player": p} for mp, p in get_active_players(match_id, db)]
    bench = [{"mp": mp, "player": p} for mp, p in match_player_repo.get_bench(db, match_id)]
    events = get_recent_events(match_id, db)
    return templates.TemplateResponse("live/index.html", {
        "request": request,
        "match": match,
        "starters": starters,
        "bench": bench,
        "events": events,
    })


@router.get("/{match_id}/summary", response_class=HTMLResponse)
async def summary_view(request: Request, match_id: str, db: Session = Depends(get_db)):
    """Render the post-match summary with participant stats and substitution history."""
    data = stats_service.get_match_summary(db, match_id)
    return templates.TemplateResponse("live/summary.html", {"request": request, **data})
