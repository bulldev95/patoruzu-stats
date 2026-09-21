"""Statistics endpoints: team history and player totals."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models import Event, Match, Player
from utils.match_utils import accumulate_player_stat, accumulate_team_stat

router = APIRouter(prefix="/stats")
templates = Jinja2Templates(directory="templates")


@router.get("/team", response_class=HTMLResponse)
async def team_stats(request: Request, db: Session = Depends(get_db)):
    matches = (
        db.query(Match)
        .filter(Match.status == "finished")
        .order_by(Match.date.desc())
        .all()
    )

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
    players = (
        db.query(Player)
        .filter(Player.games_played > 0)
        .order_by(Player.surname)
        .all()
    )

    return templates.TemplateResponse("stats/players.html", {
        "request": request,
        "players": players,
    })
