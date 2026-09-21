"""Match repository: all database queries related to the Match model."""
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models import Match


def get_by_id(db: Session, match_id: str) -> Match | None:
    """Return a match by primary key, or None if not found."""
    return db.query(Match).filter_by(id=match_id).first()


def get_or_404(db: Session, match_id: str) -> Match:
    """Return a match by primary key, raising HTTP 404 if not found."""
    match = get_by_id(db, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match


def list_finished(db: Session) -> list[Match]:
    """Return all finished matches ordered by date descending."""
    return (
        db.query(Match)
        .filter(Match.status == "finished")
        .order_by(Match.date.desc())
        .all()
    )
