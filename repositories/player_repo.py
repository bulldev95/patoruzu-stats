"""Player repository: all database queries related to the Player model."""
from sqlalchemy.orm import Session
from models import Player


def get_by_id(db: Session, player_id: str) -> Player | None:
    """Return a player by primary key, or None if not found."""
    return db.query(Player).filter_by(id=player_id).first()


def get_by_personal_id(db: Session, personal_id: str) -> Player | None:
    """Return a player by DNI (personal_id), or None if not found."""
    return db.query(Player).filter_by(personal_id=personal_id).first()


def list_with_games(db: Session) -> list[Player]:
    """Return all players who have played at least one match, sorted by surname."""
    return (
        db.query(Player)
        .filter(Player.games_played > 0)
        .order_by(Player.surname)
        .all()
    )
