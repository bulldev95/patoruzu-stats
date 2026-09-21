"""Live match view endpoints: match display, summary, and close."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models import Event, Substitution
from repositories import match_repo, match_player_repo, player_repo
from utils.match_utils import accumulate_player_stat, accumulate_team_stat, get_active_players, get_recent_events

router = APIRouter(prefix="/live")
templates = Jinja2Templates(directory="templates")


@router.get("/{match_id}", response_class=HTMLResponse)
async def live_view(request: Request, match_id: str, db: Session = Depends(get_db)):
    match = match_repo.get_or_404(db, match_id)

    active = get_active_players(match_id, db)
    starters = [{"mp": mp, "player": p} for mp, p in active]
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
    match = match_repo.get_or_404(db, match_id)
    total_minutes = match.accumulated_time // 60000

    all_mp = match_player_repo.get_all_with_players(db, match_id)
    own_events = db.query(Event).filter_by(match_id=match_id, team="own").all()

    player_event_stats: dict[str, dict] = {}
    collective: dict = {}
    for ev in own_events:
        accumulate_player_stat(collective, ev.type, ev.result)
        accumulate_team_stat(collective, ev.type, ev.result)
        if ev.player_id:
            if ev.player_id not in player_event_stats:
                player_event_stats[ev.player_id] = {}
            accumulate_player_stat(player_event_stats[ev.player_id], ev.type, ev.result)

    participants = []
    for mp, player in all_mp:
        if mp.minute_in < 0:
            continue
        minute_out = mp.minute_out if mp.minute_out is not None else total_minutes
        minutes = max(0, minute_out - mp.minute_in)
        participants.append({
            "mp": mp,
            "player": player,
            "minutes": minutes,
            "stats": player_event_stats.get(player.id, {}),
        })

    subs = db.query(Substitution).filter_by(match_id=match_id).order_by(Substitution.minute).all()
    sub_details = []
    for sub in subs:
        sub_details.append({
            "sub": sub,
            "player_out": player_repo.get_by_id(db, sub.player_out_id),
            "player_in": player_repo.get_by_id(db, sub.player_in_id),
        })

    return templates.TemplateResponse("live/summary.html", {
        "request": request,
        "match": match,
        "participants": participants,
        "collective": collective,
        "substitutions": sub_details,
        "total_minutes": total_minutes,
    })
