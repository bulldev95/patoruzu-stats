from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models import Match, MatchPlayer, Player

router = APIRouter(prefix="/live")
templates = Jinja2Templates(directory="templates")


@router.get("/{match_id}", response_class=HTMLResponse)
async def live_view(request: Request, match_id: str, db: Session = Depends(get_db)):
    match = db.query(Match).filter_by(id=match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    roster = (
        db.query(MatchPlayer, Player)
        .join(Player, MatchPlayer.player_id == Player.id)
        .filter(MatchPlayer.match_id == match_id)
        .order_by(MatchPlayer.number)
        .all()
    )

    starters = [
        {"mp": mp, "player": p} for mp, p in roster if mp.is_starter and mp.minute_out is None
    ]
    bench = [
        {"mp": mp, "player": p} for mp, p in roster if not mp.is_starter and mp.minute_out is None
    ]

    return templates.TemplateResponse("live/index.html", {
        "request": request,
        "match": match,
        "starters": starters,
        "bench": bench,
    })
