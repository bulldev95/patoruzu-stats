from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models import Match, MatchPlayer, Player
from utils.match_utils import get_active_players, get_recent_events

router = APIRouter(prefix="/live")
templates = Jinja2Templates(directory="templates")


@router.get("/{match_id}", response_class=HTMLResponse)
async def live_view(request: Request, match_id: str, db: Session = Depends(get_db)):
    match = db.query(Match).filter_by(id=match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

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

    events = get_recent_events(match_id, db)

    return templates.TemplateResponse("live/index.html", {
        "request": request,
        "match": match,
        "starters": starters,
        "bench": bench,
        "events": events,
    })
