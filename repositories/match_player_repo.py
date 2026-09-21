"""MatchPlayer repository: all database queries related to the MatchPlayer join table."""
from sqlalchemy.orm import Session
from models import MatchPlayer, Player


def get_by_match_and_player(db: Session, match_id: str, player_id: str) -> MatchPlayer | None:
    """Return the MatchPlayer record for a specific player in a specific match, or None."""
    return db.query(MatchPlayer).filter_by(match_id=match_id, player_id=player_id).first()


def get_bench(db: Session, match_id: str) -> list[tuple[MatchPlayer, Player]]:
    """Return bench players who haven't come on yet (is_starter=False, minute_in=-1)."""
    return (
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


def get_all_with_players(db: Session, match_id: str) -> list[tuple[MatchPlayer, Player]]:
    """Return all MatchPlayer rows for a match joined with their Player record, ordered by number."""
    return (
        db.query(MatchPlayer, Player)
        .join(Player, MatchPlayer.player_id == Player.id)
        .filter(MatchPlayer.match_id == match_id)
        .order_by(MatchPlayer.number)
        .all()
    )
