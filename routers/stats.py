"""Statistics endpoints: team history, player totals, and per-match player breakdown."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from repositories import player_repo
from services import stats_service

router = APIRouter(prefix="/stats")
templates = Jinja2Templates(directory="templates")


@router.get("/team", response_class=HTMLResponse)
async def team_stats(request: Request, db: Session = Depends(get_db)):
    """Render team-wide win/loss/draw totals and collective event stats."""
    data = stats_service.get_team_stats(db)
    return templates.TemplateResponse("stats/team.html", {"request": request, **data})


@router.get("/players", response_class=HTMLResponse)
async def player_stats(request: Request, db: Session = Depends(get_db)):
    """Render the player list with career totals."""
    players = player_repo.list_with_games(db)
    return templates.TemplateResponse("stats/players.html", {"request": request, "players": players})


@router.get("/players/{player_id}", response_class=HTMLResponse)
async def player_detail(player_id: str, request: Request, db: Session = Depends(get_db)):
    """Render a player's historical totals and per-match stat breakdown."""
    data = stats_service.get_player_detail(db, player_id)
    if data is None:
        return RedirectResponse(url="/stats/players", status_code=302)
    return templates.TemplateResponse("stats/player_detail.html", {"request": request, **data})
