import os
import uuid
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models import Match, MatchPlayer, Player
from utils.pdf_parser import parse_team_sheet, save_upload_to_tempfile

router = APIRouter(prefix="/setup")
templates = Jinja2Templates(directory="templates")

POSITIONS = {
    1: "Prop", 2: "Hooker", 3: "Prop",
    4: "Lock", 5: "Lock",
    6: "Flanker", 7: "Flanker", 8: "Number 8",
    9: "Scrum-half", 10: "Fly-half",
    11: "Wing", 12: "Centre", 13: "Centre", 14: "Wing", 15: "Fullback",
}


@router.get("/", response_class=HTMLResponse)
async def setup_page(request: Request):
    return templates.TemplateResponse("setup/upload.html", {"request": request})


@router.post("/upload", response_class=HTMLResponse)
async def upload_pdf(request: Request, file: UploadFile = File(...)):
    tmp_path = await save_upload_to_tempfile(file)
    try:
        data = parse_team_sheet(tmp_path)
    except Exception:
        return templates.TemplateResponse("setup/upload.html", {
            "request": request,
            "error": "Invalid PDF format. Please upload the official UAR squad sheet from bd.uar.com.ar.",
        })
    finally:
        os.unlink(tmp_path)

    return templates.TemplateResponse("setup/confirm.html", {
        "request": request,
        "data": data,
        "positions": POSITIONS,
    })


@router.post("/confirm")
async def confirm_setup(
    request: Request,
    db: Session = Depends(get_db),
    date: str = Form(...),
    rival: str = Form(...),
    competition: str = Form(...),
    venue: str = Form(""),
):
    form = await request.form()

    match = Match(
        id=str(uuid.uuid4()),
        date=date,
        rival=rival,
        competition=competition,
        venue=venue or None,
    )
    db.add(match)
    db.flush()

    indices = [k.split("_")[1] for k in form.keys() if k.startswith("number_")]
    for idx in indices:
        number = int(form[f"number_{idx}"])
        surname = form[f"surname_{idx}"]
        name = form[f"name_{idx}"]
        personal_id = form[f"personal_id_{idx}"]

        player = db.query(Player).filter_by(personal_id=personal_id).first()
        if not player:
            player = Player(personal_id=personal_id, surname=surname, name=name)
            db.add(player)
            db.flush()
        else:
            player.surname = surname
            player.name = name

        mp = MatchPlayer(
            match_id=match.id,
            player_id=player.id,
            number=number,
            position=POSITIONS.get(number) if number <= 15 else None,
            is_starter=number <= 15,
            minute_in=0,
        )
        db.add(mp)

    db.commit()
    return RedirectResponse(url=f"/live/{match.id}", status_code=303)
