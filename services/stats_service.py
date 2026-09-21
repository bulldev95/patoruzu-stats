"""Business logic for statistics views: team totals, player detail, and match summary."""
from sqlalchemy.orm import Session

from models import Event, Match, MatchPlayer, Substitution
from repositories import match_player_repo, match_repo, player_repo
from utils.match_utils import accumulate_player_stat, accumulate_team_stat


def get_team_stats(db: Session) -> dict:
    """Aggregate win/loss/draw totals and collective event stats across all finished matches.

    Returns a dict with keys: matches, totals, collective.
    """
    matches = match_repo.list_finished(db)
    totals = {
        "matches": len(matches),
        "wins":    sum(1 for m in matches if m.score_own > m.score_rival),
        "losses":  sum(1 for m in matches if m.score_own < m.score_rival),
        "draws":   sum(1 for m in matches if m.score_own == m.score_rival),
        "points_for":     sum(m.score_own for m in matches),
        "points_against": sum(m.score_rival for m in matches),
    }
    collective: dict = {}
    match_ids = [m.id for m in matches]
    if match_ids:
        own_events = (
            db.query(Event)
            .filter(Event.match_id.in_(match_ids), Event.team == "own")
            .all()
        )
        for ev in own_events:
            accumulate_player_stat(collective, ev.type, ev.result)
            accumulate_team_stat(collective, ev.type, ev.result)
    return {"matches": matches, "totals": totals, "collective": collective}


def get_player_detail(db: Session, player_id: str) -> dict | None:
    """Return per-match stat breakdown for a player across all finished matches.

    Returns None if the player does not exist.
    Returns a dict with keys: player, match_stats (list of {match, minutes, stats}).
    """
    player = player_repo.get_by_id(db, player_id)
    if not player:
        return None

    match_players = (
        db.query(MatchPlayer)
        .join(Match, MatchPlayer.match_id == Match.id)
        .filter(MatchPlayer.player_id == player_id, Match.status == "finished")
        .order_by(Match.date.desc())
        .all()
    )

    match_stats = []
    for mp in match_players:
        stats: dict = {}
        events = (
            db.query(Event)
            .filter(Event.match_id == mp.match_id, Event.player_id == player_id, Event.team == "own")
            .all()
        )
        for ev in events:
            accumulate_player_stat(stats, ev.type, ev.result)

        total_minutes = max(0, mp.match.accumulated_time // 60000)
        minutes = 0 if mp.minute_in < 0 else max(0, (mp.minute_out or total_minutes) - mp.minute_in)
        match_stats.append({"match": mp.match, "minutes": minutes, "stats": stats})

    return {"player": player, "match_stats": match_stats}


def get_match_summary(db: Session, match_id: str) -> dict:
    """Compute full match summary: participant stats, collective event totals, and substitution details.

    Returns a dict with keys: match, participants, collective, substitutions, total_minutes.
    """
    match = match_repo.get_or_404(db, match_id)
    total_minutes = match.accumulated_time // 60000
    all_mp = match_player_repo.get_all_with_players(db, match_id)
    own_events = db.query(Event).filter_by(match_id=match_id, team="own").all()

    player_event_stats: dict[str, dict] = {}
    collective: dict = {}
    for ev in own_events:
        accumulate_player_stat(collective, ev.type, ev.result)
        accumulate_team_stat(collective, ev.type, ev.result)
        if ev.player_id:
            if ev.player_id not in player_event_stats:
                player_event_stats[ev.player_id] = {}
            accumulate_player_stat(player_event_stats[ev.player_id], ev.type, ev.result)

    participants = []
    for mp, player in all_mp:
        if mp.minute_in < 0:
            continue
        minute_out = mp.minute_out if mp.minute_out is not None else total_minutes
        participants.append({
            "mp": mp,
            "player": player,
            "minutes": max(0, minute_out - mp.minute_in),
            "stats": player_event_stats.get(player.id, {}),
        })

    subs = db.query(Substitution).filter_by(match_id=match_id).order_by(Substitution.minute).all()
    sub_details = [
        {
            "sub": sub,
            "player_out": player_repo.get_by_id(db, sub.player_out_id),
            "player_in":  player_repo.get_by_id(db, sub.player_in_id),
        }
        for sub in subs
    ]

    return {
        "match": match,
        "participants": participants,
        "collective": collective,
        "substitutions": sub_details,
        "total_minutes": total_minutes,
    }
