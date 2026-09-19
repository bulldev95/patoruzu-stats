from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from database import Base, engine
import models  # noqa: F401 — registers models with Base

Base.metadata.create_all(bind=engine)

# Migración paso 9: bench players creados antes usaban minute_in=0; ahora usan -1
with engine.connect() as _conn:
    _conn.execute(text(
        "UPDATE match_players SET minute_in = -1 "
        "WHERE is_starter = 0 AND minute_in = 0 AND minute_out IS NULL "
        "AND player_id NOT IN ("
        "  SELECT player_in_id FROM substitutions WHERE match_id = match_players.match_id"
        ")"
    ))
    _conn.commit()

app = FastAPI(title="Patoruzú Stats")

app.mount("/static", StaticFiles(directory="static"), name="static")

from routers import setup, live, actions  # noqa: E402
app.include_router(setup.router)
app.include_router(live.router)
app.include_router(actions.router)


@app.get("/")
async def index():
    return RedirectResponse(url="/setup/")
