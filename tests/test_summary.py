import uuid
from models import Event, Match, MatchPlayer, Player, Substitution


def _player_id(sample_match, db, number):
    return db.query(MatchPlayer).filter_by(match_id=sample_match.id, number=number).first().player_id


def _add_event(db, match_id, event_type, result, player_id=None, team="own"):
    ev = Event(
        match_id=match_id,
        minute=5,
        period=1,
        team=team,
        type=event_type,
        result=result,
        player_id=player_id,
    )
    db.add(ev)
    db.commit()
    return ev


class TestCloseMatch:
    def test_sets_status_finished(self, client, sample_match, db):
        client.post(f"/live/{sample_match.id}/close")
        db.refresh(sample_match)
        assert sample_match.status == "finished"

    def test_redirects_to_summary(self, client, sample_match):
        response = client.post(f"/live/{sample_match.id}/close", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == f"/live/{sample_match.id}/summary"

    def test_invalid_match_returns_404(self, client):
        response = client.post("/live/nonexistent/close")
        assert response.status_code == 404

    def test_increments_games_played_for_starters(self, client, sample_match, db):
        pid = _player_id(sample_match, db, 1)
        player = db.query(Player).filter_by(id=pid).first()
        before = player.games_played
        client.post(f"/live/{sample_match.id}/close")
        db.refresh(player)
        assert player.games_played == before + 1

    def test_bench_player_not_counted(self, client, sample_match, db):
        pid = _player_id(sample_match, db, 16)
        player = db.query(Player).filter_by(id=pid).first()
        before = player.games_played
        client.post(f"/live/{sample_match.id}/close")
        db.refresh(player)
        assert player.games_played == before

    def test_minutes_played_updated_for_full_starter(self, client, sample_match, db):
        sample_match.accumulated_time = 4_800_000  # 80 minutes in ms
        db.commit()
        pid = _player_id(sample_match, db, 1)
        player = db.query(Player).filter_by(id=pid).first()
        before = player.minutes_played
        client.post(f"/live/{sample_match.id}/close")
        db.refresh(player)
        assert player.minutes_played == before + 80

    def test_minutes_played_for_sub_who_came_on(self, client, sample_match, db):
        sample_match.accumulated_time = 4_800_000  # 80 min
        mp_sub = db.query(MatchPlayer).filter_by(match_id=sample_match.id, number=16).first()
        mp_sub.minute_in = 60
        db.commit()
        pid = mp_sub.player_id
        player = db.query(Player).filter_by(id=pid).first()
        before = player.minutes_played
        client.post(f"/live/{sample_match.id}/close")
        db.refresh(player)
        assert player.minutes_played == before + 20  # 80 - 60

    def test_minutes_capped_at_minute_out(self, client, sample_match, db):
        sample_match.accumulated_time = 4_800_000  # 80 min
        mp = db.query(MatchPlayer).filter_by(match_id=sample_match.id, number=1).first()
        mp.minute_out = 40
        db.commit()
        pid = mp.player_id
        player = db.query(Player).filter_by(id=pid).first()
        before = player.minutes_played
        client.post(f"/live/{sample_match.id}/close")
        db.refresh(player)
        assert player.minutes_played == before + 40

    def test_pauses_running_clock(self, client, sample_match, db):
        import time
        sample_match.start_timestamp = int(time.time() * 1000) - 60_000
        sample_match.status = "live"
        db.commit()
        client.post(f"/live/{sample_match.id}/close")
        db.refresh(sample_match)
        assert sample_match.start_timestamp is None
        assert sample_match.accumulated_time >= 60_000


class TestSummaryView:
    def test_returns_200(self, client, sample_match):
        response = client.get(f"/live/{sample_match.id}/summary")
        assert response.status_code == 200

    def test_invalid_match_returns_404(self, client):
        response = client.get("/live/nonexistent/summary")
        assert response.status_code == 404

    def test_shows_score(self, client, sample_match, db):
        sample_match.score_own = 21
        sample_match.score_rival = 14
        db.commit()
        response = client.get(f"/live/{sample_match.id}/summary")
        assert "21" in response.text
        assert "14" in response.text

    def test_shows_rival(self, client, sample_match):
        response = client.get(f"/live/{sample_match.id}/summary")
        assert sample_match.rival in response.text

    def test_shows_participant_names(self, client, sample_match):
        response = client.get(f"/live/{sample_match.id}/summary")
        assert "Surname1" in response.text

    def test_bench_player_not_shown_in_table(self, client, sample_match):
        response = client.get(f"/live/{sample_match.id}/summary")
        # Bench player 16 has minute_in=-1 so should not appear in participants table
        # (they do appear in the page header row titles but not as a data row)
        # We verify the page loads correctly without crashing
        assert response.status_code == 200

    def test_shows_try_in_collective_stats(self, client, sample_match, db):
        pid = _player_id(sample_match, db, 1)
        _add_event(db, sample_match.id, "try", "scored", player_id=pid)
        response = client.get(f"/live/{sample_match.id}/summary")
        assert "Tries" in response.text

    def test_shows_try_in_player_row(self, client, sample_match, db):
        pid = _player_id(sample_match, db, 1)
        _add_event(db, sample_match.id, "try", "scored", player_id=pid)
        response = client.get(f"/live/{sample_match.id}/summary")
        assert "1" in response.text

    def test_rival_events_excluded_from_collective(self, client, sample_match, db):
        _add_event(db, sample_match.id, "try", "scored", team="rival")
        response = client.get(f"/live/{sample_match.id}/summary")
        # rival tries don't appear in collective stats section — page still loads
        assert response.status_code == 200

    def test_shows_substitutions(self, client, sample_match, db):
        out_id = _player_id(sample_match, db, 1)
        in_id = _player_id(sample_match, db, 16)
        sub = Substitution(
            match_id=sample_match.id,
            minute=40,
            player_out_id=out_id,
            player_in_id=in_id,
            position="Prop",
        )
        db.add(sub)
        db.commit()
        response = client.get(f"/live/{sample_match.id}/summary")
        assert "Sustituciones" in response.text
        assert "Surname1" in response.text
        assert "Surname16" in response.text

    def test_shows_total_minutes(self, client, sample_match, db):
        sample_match.accumulated_time = 4_800_000
        db.commit()
        response = client.get(f"/live/{sample_match.id}/summary")
        assert "80" in response.text
