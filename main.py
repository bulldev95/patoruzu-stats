from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from database import Base, engine
import models  # noqa: F401 — registers models with Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Patoruzú Stats")

app.mount("/static", StaticFiles(directory="static"), name="static")

from routers import setup, live, actions  # noqa: E402
app.include_router(setup.router)
app.include_router(live.router)
app.include_router(actions.router)


@app.get("/")
async def index():
    return RedirectResponse(url="/setup/")
