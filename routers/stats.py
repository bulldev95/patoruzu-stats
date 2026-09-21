"""Statistics endpoints: team history, player totals, and per-match player breakdown."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models import Event, Match, MatchPlayer
from repositories import match_repo, player_repo
from utils.match_utils import accumulate_player_stat, accumulate_team_stat

router = APIRouter(prefix="/stats")
templates = Jinja2Templates(directory="templates")


@router.get("/team", response_class=HTMLResponse)
async def team_stats(request: Request, db: Session = Depends(get_db)):
    matches = match_repo.list_finished(db)

    totals = {
        "matches": len(matches),
        "wins": sum(1 for m in matches if m.score_own > m.score_rival),
        "losses": sum(1 for m in matches if m.score_own < m.score_rival),
        "draws": sum(1 for m in matches if m.score_own == m.score_rival),
        "points_for": sum(m.score_own for m in matches),
        "points_against": sum(m.score_rival for m in matches),
    }

    match_ids = [m.id for m in matches]
    collective: dict = {}
    if match_ids:
        own_events = (
            db.query(Event)
            .filter(Event.match_id.in_(match_ids), Event.team == "own")
            .all()
        )
        for ev in own_events:
            accumulate_player_stat(collective, ev.type, ev.result)
            accumulate_team_stat(collective, ev.type, ev.result)

    return templates.TemplateResponse("stats/team.html", {
        "request": request,
        "matches": matches,
        "totals": totals,
        "collective": collective,
    })


@router.get("/players", response_class=HTMLResponse)
async def player_stats(request: Request, db: Session = Depends(get_db)):
    players = player_repo.list_with_games(db)
    return templates.TemplateResponse("stats/players.html", {
        "request": request,
        "players": players,
    })


@router.get("/players/{player_id}", response_class=HTMLResponse)
async def player_detail(player_id: str, request: Request, db: Session = Depends(get_db)):
    """Render a player's historical totals and per-match stat breakdown, computed on-the-fly from events."""
    player = player_repo.get_by_id(db, player_id)
    if not player:
        return RedirectResponse(url="/stats/players", status_code=302)

    match_players = (
        db.query(MatchPlayer)
        .join(Match, MatchPlayer.match_id == Match.id)
        .filter(MatchPlayer.player_id == player_id, Match.status == "finished")
        .order_by(Match.date.desc())
        .all()
    )

    match_stats = []
    for mp in match_players:
        stats: dict = {}
        events = (
            db.query(Event)
            .filter(
                Event.match_id == mp.match_id,
                Event.player_id == player_id,
                Event.team == "own",
            )
            .all()
        )
        for ev in events:
            accumulate_player_stat(stats, ev.type, ev.result)

        total_minutes = max(0, mp.match.accumulated_time // 60000)
        if mp.minute_in < 0:
            minutes = 0
        else:
            minute_out = mp.minute_out if mp.minute_out is not None else total_minutes
            minutes = max(0, minute_out - mp.minute_in)

        match_stats.append({
            "match": mp.match,
            "minutes": minutes,
            "stats": stats,
        })

    return templates.TemplateResponse("stats/player_detail.html", {
        "request": request,
        "player": player,
        "match_stats": match_stats,
    })
