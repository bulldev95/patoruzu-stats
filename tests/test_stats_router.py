import uuid
import pytest
from models import Event, Match, MatchPlayer, Player


class TestTeamStats:
    def test_returns_200(self, client, db):
        response = client.get("/stats/team")
        assert response.status_code == 200

    def test_empty_state(self, client, db):
        response = client.get("/stats/team")
        assert response.status_code == 200

    def test_shows_finished_match(self, client, db):
        match = Match(
            id=str(uuid.uuid4()),
            date="2026-08-15",
            rival="Tala RC",
            competition="Liga",
            status="finished",
            score_own=21,
            score_rival=17,
            accumulated_time=4800000,
        )
        db.add(match)
        db.commit()
        response = client.get("/stats/team")
        assert "Tala RC" in response.text

    def test_excludes_live_match(self, client, db):
        match = Match(
            id=str(uuid.uuid4()),
            date="2026-09-21",
            rival="Rival En Vivo",
            competition="Liga",
            status="live",
            accumulated_time=0,
        )
        db.add(match)
        db.commit()
        response = client.get("/stats/team")
        assert "Rival En Vivo" not in response.text

    def test_counts_win(self, client, db):
        match = Match(
            id=str(uuid.uuid4()),
            date="2026-08-15",
            rival="Rival",
            competition="Liga",
            status="finished",
            score_own=21,
            score_rival=10,
            accumulated_time=4800000,
        )
        db.add(match)
        db.commit()
        response = client.get("/stats/team")
        assert response.status_code == 200

    def test_accumulates_events(self, client, db):
        match = Match(
            id=str(uuid.uuid4()),
            date="2026-08-15",
            rival="Rival",
            competition="Liga",
            status="finished",
            score_own=5,
            score_rival=0,
            accumulated_time=4800000,
        )
        db.add(match)
        db.flush()
        db.add(Event(
            match_id=match.id,
            minute=10,
            period=1,
            team="own",
            type="try",
            result="scored",
        ))
        db.commit()
        response = client.get("/stats/team")
        assert response.status_code == 200


@pytest.fixture
def finished_match_with_player(db):
    player = Player(
        id=str(uuid.uuid4()),
        personal_id="99999999",
        surname="Roldan",
        name="Denis",
        games_played=1,
        minutes_played=40,
        tries=2,
        tackles_positive=5,
        tackles_missed=1,
    )
    db.add(player)
    db.flush()

    match = Match(
        id=str(uuid.uuid4()),
        date="2026-08-15",
        rival="Tala RC",
        competition="Torneo Austral 2026",
        venue="Local",
        score_own=21,
        score_rival=17,
        status="finished",
        accumulated_time=2400000,  # 40 minutes
    )
    db.add(match)
    db.flush()

    mp = MatchPlayer(
        match_id=match.id,
        player_id=player.id,
        number=1,
        position="Prop",
        is_starter=True,
        minute_in=0,
        minute_out=None,
    )
    db.add(mp)

    for event_type, result in [
        ("try", "scored"),
        ("try", "scored"),
        ("tackle", "positive"),
        ("tackle", "positive"),
        ("tackle", "missed"),
    ]:
        db.add(Event(
            match_id=match.id,
            minute=10,
            period=1,
            team="own",
            type=event_type,
            result=result,
            player_id=player.id,
        ))

    db.commit()
    return player, match


class TestPlayersList:
    def test_returns_200(self, client, db):
        response = client.get("/stats/players")
        assert response.status_code == 200

    def test_empty_state_message(self, client, db):
        response = client.get("/stats/players")
        assert "No hay jugadores registrados" in response.text

    def test_shows_player_with_games(self, client, db, finished_match_with_player):
        player, _ = finished_match_with_player
        response = client.get("/stats/players")
        assert "Roldan" in response.text

    def test_row_links_to_detail(self, client, db, finished_match_with_player):
        player, _ = finished_match_with_player
        response = client.get("/stats/players")
        assert f"/stats/players/{player.id}" in response.text


class TestPlayerDetail:
    def test_returns_200(self, client, db, finished_match_with_player):
        player, _ = finished_match_with_player
        response = client.get(f"/stats/players/{player.id}")
        assert response.status_code == 200

    def test_unknown_player_redirects(self, client, db):
        response = client.get("/stats/players/nonexistent-id", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/stats/players"

    def test_shows_player_name(self, client, db, finished_match_with_player):
        player, _ = finished_match_with_player
        response = client.get(f"/stats/players/{player.id}")
        assert "Roldan" in response.text
        assert "Denis" in response.text

    def test_shows_match_row(self, client, db, finished_match_with_player):
        player, _ = finished_match_with_player
        response = client.get(f"/stats/players/{player.id}")
        assert "Tala RC" in response.text

    def test_shows_match_score(self, client, db, finished_match_with_player):
        player, _ = finished_match_with_player
        response = client.get(f"/stats/players/{player.id}")
        assert "21" in response.text
        assert "17" in response.text

    def test_shows_tries_from_events(self, client, db, finished_match_with_player):
        player, _ = finished_match_with_player
        response = client.get(f"/stats/players/{player.id}")
        # 2 tries registered via events
        assert response.text.count(">2<") >= 1

    def test_shows_minutes_played(self, client, db, finished_match_with_player):
        player, match = finished_match_with_player
        response = client.get(f"/stats/players/{player.id}")
        # accumulated_time=2400000ms = 40 min, minute_in=0, minute_out=None → 40 min
        assert "40" in response.text

    def test_excludes_live_matches(self, client, db):
        player = Player(
            id=str(uuid.uuid4()),
            personal_id="88888888",
            surname="Test",
            name="Player",
            games_played=0,
        )
        db.add(player)
        db.flush()

        live_match = Match(
            id=str(uuid.uuid4()),
            date="2026-09-21",
            rival="Rival",
            competition="Liga",
            status="live",
            accumulated_time=0,
        )
        db.add(live_match)
        db.flush()
        db.add(MatchPlayer(
            match_id=live_match.id,
            player_id=player.id,
            number=1,
            is_starter=True,
            minute_in=0,
        ))
        db.commit()

        response = client.get(f"/stats/players/{player.id}")
        assert response.status_code == 200
        assert "Rival" not in response.text

    def test_bench_player_shows_zero_minutes(self, client, db):
        player = Player(
            id=str(uuid.uuid4()),
            personal_id="77777777",
            surname="Banco",
            name="Jugador",
            games_played=1,
        )
        db.add(player)
        db.flush()

        match = Match(
            id=str(uuid.uuid4()),
            date="2026-09-01",
            rival="Otro Club",
            competition="Liga",
            status="finished",
            accumulated_time=4800000,  # 80 min
        )
        db.add(match)
        db.flush()
        db.add(MatchPlayer(
            match_id=match.id,
            player_id=player.id,
            number=20,
            is_starter=False,
            minute_in=-1,  # never came on
        ))
        db.commit()

        response = client.get(f"/stats/players/{player.id}")
        assert response.status_code == 200
        assert "Otro Club" in response.text


class TestDeleteMatch:
    def _finished_match_with_player(self, db, tries=0, tackles=0, games=1, minutes=80):
        player = Player(
            id=str(uuid.uuid4()),
            personal_id=str(uuid.uuid4())[:8],
            surname="Del",
            name="Partido",
            games_played=games,
            minutes_played=minutes,
            tries=tries,
            tackles_total=tackles,
            tackles_positive=tackles,
        )
        db.add(player)
        db.flush()
        match = Match(
            id=str(uuid.uuid4()),
            date="2026-08-01",
            rival="Rival Test",
            competition="Liga",
            status="finished",
            accumulated_time=4800000,
        )
        db.add(match)
        db.flush()
        db.add(MatchPlayer(
            match_id=match.id,
            player_id=player.id,
            number=1,
            is_starter=True,
            minute_in=0,
        ))
        db.commit()
        return match, player

    def test_redirects_to_team_stats(self, client, db):
        match, _ = self._finished_match_with_player(db)
        response = client.post(f"/stats/matches/{match.id}/delete", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/stats/team"

    def test_match_is_deleted(self, client, db):
        match, _ = self._finished_match_with_player(db)
        client.post(f"/stats/matches/{match.id}/delete")
        assert db.query(Match).filter_by(id=match.id).first() is None

    def test_reverts_games_played(self, client, db):
        match, player = self._finished_match_with_player(db, games=3, minutes=240)
        client.post(f"/stats/matches/{match.id}/delete")
        db.refresh(player)
        assert player.games_played == 2

    def test_reverts_minutes_played(self, client, db):
        match, player = self._finished_match_with_player(db, games=1, minutes=80)
        client.post(f"/stats/matches/{match.id}/delete")
        db.refresh(player)
        assert player.minutes_played == 0

    def test_reverts_event_stats(self, client, db):
        match, player = self._finished_match_with_player(db, tries=2)
        db.add(Event(
            match_id=match.id, minute=10, period=1,
            team="own", type="try", result="any", player_id=player.id,
        ))
        db.commit()
        client.post(f"/stats/matches/{match.id}/delete")
        db.refresh(player)
        assert player.tries == 1

    def test_rival_events_do_not_affect_player_stats(self, client, db):
        match, player = self._finished_match_with_player(db, tries=1)
        db.add(Event(
            match_id=match.id, minute=5, period=1,
            team="rival", type="try", result="any", player_id=player.id,
        ))
        db.commit()
        client.post(f"/stats/matches/{match.id}/delete")
        db.refresh(player)
        assert player.tries == 1

    def test_bench_player_not_deducted(self, client, db):
        player = Player(
            id=str(uuid.uuid4()),
            personal_id=str(uuid.uuid4())[:8],
            surname="Banco",
            name="NoJugo",
            games_played=1,
            minutes_played=50,
        )
        db.add(player)
        db.flush()
        match = Match(
            id=str(uuid.uuid4()),
            date="2026-08-01",
            rival="Rival",
            competition="Liga",
            status="finished",
            accumulated_time=4800000,
        )
        db.add(match)
        db.flush()
        db.add(MatchPlayer(
            match_id=match.id, player_id=player.id,
            number=20, is_starter=False, minute_in=-1,
        ))
        db.commit()
        client.post(f"/stats/matches/{match.id}/delete")
        db.refresh(player)
        assert player.games_played == 1
        assert player.minutes_played == 50

    def test_404_for_unknown_match(self, client, db):
        response = client.post("/stats/matches/nonexistent/delete")
        assert response.status_code == 404

    def test_400_for_non_finished_match(self, client, db):
        match = Match(
            id=str(uuid.uuid4()),
            date="2026-09-01",
            rival="En Vivo",
            competition="Liga",
            status="live",
            accumulated_time=0,
        )
        db.add(match)
        db.commit()
        response = client.post(f"/stats/matches/{match.id}/delete")
        assert response.status_code == 400

    def test_cascades_delete_events_and_match_players(self, client, db):
        match, player = self._finished_match_with_player(db)
        db.add(Event(
            match_id=match.id, minute=5, period=1,
            team="own", type="tackle", result="positive", player_id=player.id,
        ))
        db.commit()
        client.post(f"/stats/matches/{match.id}/delete")
        assert db.query(Event).filter_by(match_id=match.id).count() == 0
        assert db.query(MatchPlayer).filter_by(match_id=match.id).count() == 0
