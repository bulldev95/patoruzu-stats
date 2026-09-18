from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from database import Base, engine
import models  # noqa: F401 — registra los modelos en Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Patoruzú Stats")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
