"""Statistics endpoints: team history and player totals."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models import Match, Player

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

    return templates.TemplateResponse("stats/team.html", {
        "request": request,
        "matches": matches,
        "totals": totals,
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
