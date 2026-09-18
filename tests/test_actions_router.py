import time
from models import Event, Match


def event_form(event_type="tackle", result="positive", **extra):
    data = {"type": event_type, "result": result}
    data.update(extra)
    return data


class TestClockStart:
    def test_sets_start_timestamp(self, client, sample_match, db):
        client.post(f"/live/{sample_match.id}/clock/start")
        db.refresh(sample_match)
        assert sample_match.start_timestamp is not None

    def test_sets_status_live(self, client, sample_match, db):
        client.post(f"/live/{sample_match.id}/clock/start")
        db.refresh(sample_match)
        assert sample_match.status == "live"

    def test_returns_clock_html(self, client, sample_match):
        response = client.post(f"/live/{sample_match.id}/clock/start")
        assert response.status_code == 200
        assert "clock-container" in response.text

    def test_shows_pause_button_when_running(self, client, sample_match):
        response = client.post(f"/live/{sample_match.id}/clock/start")
        assert "Pause" in response.text

    def test_no_change_if_already_running(self, client, sample_match, db):
        ts = int(time.time() * 1000) - 5000
        sample_match.start_timestamp = ts
        sample_match.status = "live"
        db.commit()
        client.post(f"/live/{sample_match.id}/clock/start")
        db.refresh(sample_match)
        assert sample_match.start_timestamp == ts  # unchanged

    def test_invalid_match_returns_404(self, client):
        response = client.post("/live/nonexistent/clock/start")
        assert response.status_code == 404


class TestClockPause:
    def test_clears_start_timestamp(self, client, sample_match, db):
        sample_match.start_timestamp = int(time.time() * 1000) - 10000
        sample_match.status = "live"
        db.commit()
        client.post(f"/live/{sample_match.id}/clock/pause")
        db.refresh(sample_match)
        assert sample_match.start_timestamp is None

    def test_accumulates_elapsed_time(self, client, sample_match, db):
        sample_match.start_timestamp = int(time.time() * 1000) - 60000  # 60s
        sample_match.accumulated_time = 0
        sample_match.status = "live"
        db.commit()
        client.post(f"/live/{sample_match.id}/clock/pause")
        db.refresh(sample_match)
        assert sample_match.accumulated_time >= 59000

    def test_sets_status_paused(self, client, sample_match, db):
        sample_match.start_timestamp = int(time.time() * 1000)
        sample_match.status = "live"
        db.commit()
        client.post(f"/live/{sample_match.id}/clock/pause")
        db.refresh(sample_match)
        assert sample_match.status == "paused"

    def test_returns_clock_html(self, client, sample_match, db):
        sample_match.start_timestamp = int(time.time() * 1000)
        sample_match.status = "live"
        db.commit()
        response = client.post(f"/live/{sample_match.id}/clock/pause")
        assert response.status_code == 200
        assert "clock-container" in response.text

    def test_shows_start_button_when_paused(self, client, sample_match, db):
        sample_match.start_timestamp = int(time.time() * 1000)
        sample_match.status = "live"
        db.commit()
        response = client.post(f"/live/{sample_match.id}/clock/pause")
        assert "Start" in response.text

    def test_no_change_if_already_paused(self, client, sample_match, db):
        sample_match.accumulated_time = 5000
        sample_match.start_timestamp = None
        db.commit()
        client.post(f"/live/{sample_match.id}/clock/pause")
        db.refresh(sample_match)
        assert sample_match.accumulated_time == 5000

    def test_invalid_match_returns_404(self, client):
        response = client.post("/live/nonexistent/clock/pause")
        assert response.status_code == 404


class TestClockNextPeriod:
    def test_advances_to_period_2(self, client, sample_match, db):
        sample_match.period = 1
        sample_match.status = "paused"
        sample_match.accumulated_time = 2400000
        db.commit()
        client.post(f"/live/{sample_match.id}/clock/next-period")
        db.refresh(sample_match)
        assert sample_match.period == 2

    def test_resets_accumulated_time(self, client, sample_match, db):
        sample_match.accumulated_time = 2400000
        sample_match.period = 1
        db.commit()
        client.post(f"/live/{sample_match.id}/clock/next-period")
        db.refresh(sample_match)
        assert sample_match.accumulated_time == 0

    def test_clears_start_timestamp(self, client, sample_match, db):
        sample_match.start_timestamp = int(time.time() * 1000)
        sample_match.period = 1
        db.commit()
        client.post(f"/live/{sample_match.id}/clock/next-period")
        db.refresh(sample_match)
        assert sample_match.start_timestamp is None

    def test_no_change_if_already_period_2(self, client, sample_match, db):
        sample_match.period = 2
        sample_match.accumulated_time = 1000
        db.commit()
        client.post(f"/live/{sample_match.id}/clock/next-period")
        db.refresh(sample_match)
        assert sample_match.period == 2
        assert sample_match.accumulated_time == 1000

    def test_returns_clock_html(self, client, sample_match, db):
        sample_match.period = 1
        db.commit()
        response = client.post(f"/live/{sample_match.id}/clock/next-period")
        assert response.status_code == 200
        assert "clock-container" in response.text

    def test_invalid_match_returns_404(self, client):
        response = client.post("/live/nonexistent/clock/next-period")
        assert response.status_code == 404


class TestActionSheetLoader:
    def test_valid_action_returns_200(self, client, sample_match):
        response = client.get(f"/live/{sample_match.id}/actions/tackle")
        assert response.status_code == 200

    def test_invalid_action_returns_404(self, client, sample_match):
        response = client.get(f"/live/{sample_match.id}/actions/nonexistent")
        assert response.status_code == 404

    def test_invalid_match_returns_404(self, client):
        response = client.get("/live/nonexistent/actions/tackle")
        assert response.status_code == 404

    def test_sheet_contains_form(self, client, sample_match):
        response = client.get(f"/live/{sample_match.id}/actions/tackle")
        assert "<form" in response.text

    def test_sheet_contains_hidden_type(self, client, sample_match):
        response = client.get(f"/live/{sample_match.id}/actions/tackle")
        assert 'name="type" value="tackle"' in response.text

    def test_try_sheet_loads(self, client, sample_match):
        response = client.get(f"/live/{sample_match.id}/actions/try")
        assert response.status_code == 200
        assert "Try" in response.text

    def test_all_valid_actions_load(self, client, sample_match):
        actions = ["tackle","try","conversion","drop","scrum","lineout",
                   "ruck","maul","penal","kick","perdida","salida","tarjeta"]
        for action in actions:
            r = client.get(f"/live/{sample_match.id}/actions/{action}")
            assert r.status_code == 200, f"{action} returned {r.status_code}"


class TestSaveEvent:
    def test_saves_event_to_db(self, client, sample_match, db):
        client.post(f"/live/{sample_match.id}/events", data=event_form())
        assert db.query(Event).filter_by(match_id=sample_match.id).count() == 1

    def test_returns_events_feed_html(self, client, sample_match):
        response = client.post(f"/live/{sample_match.id}/events", data=event_form())
        assert response.status_code == 200
        assert "<html>" not in response.text  # partial, not full page

    def test_event_has_correct_type(self, client, sample_match, db):
        client.post(f"/live/{sample_match.id}/events", data=event_form("scrum", "won"))
        event = db.query(Event).filter_by(match_id=sample_match.id).first()
        assert event.type == "scrum"
        assert event.result == "won"

    def test_event_has_period(self, client, sample_match, db):
        client.post(f"/live/{sample_match.id}/events", data=event_form())
        event = db.query(Event).filter_by(match_id=sample_match.id).first()
        assert event.period == 1

    def test_event_team_is_own(self, client, sample_match, db):
        client.post(f"/live/{sample_match.id}/events", data=event_form())
        event = db.query(Event).filter_by(match_id=sample_match.id).first()
        assert event.team == "own"

    def test_try_adds_5_points(self, client, sample_match, db):
        client.post(f"/live/{sample_match.id}/events", data=event_form("try", "scored"))
        db.refresh(sample_match)
        assert sample_match.score_own == 5

    def test_conversion_scored_adds_2_points(self, client, sample_match, db):
        client.post(f"/live/{sample_match.id}/events", data=event_form("conversion", "scored"))
        db.refresh(sample_match)
        assert sample_match.score_own == 2

    def test_conversion_missed_adds_0_points(self, client, sample_match, db):
        client.post(f"/live/{sample_match.id}/events", data=event_form("conversion", "missed"))
        db.refresh(sample_match)
        assert sample_match.score_own == 0

    def test_drop_scored_adds_3_points(self, client, sample_match, db):
        client.post(f"/live/{sample_match.id}/events", data=event_form("drop", "scored"))
        db.refresh(sample_match)
        assert sample_match.score_own == 3

    def test_drop_missed_adds_0_points(self, client, sample_match, db):
        client.post(f"/live/{sample_match.id}/events", data=event_form("drop", "missed"))
        db.refresh(sample_match)
        assert sample_match.score_own == 0

    def test_penal_kicked_adds_3_points(self, client, sample_match, db):
        client.post(f"/live/{sample_match.id}/events", data=event_form("penal", "kicked"))
        db.refresh(sample_match)
        assert sample_match.score_own == 3

    def test_penal_conceded_adds_0_points(self, client, sample_match, db):
        client.post(f"/live/{sample_match.id}/events", data=event_form("penal", "conceded"))
        db.refresh(sample_match)
        assert sample_match.score_own == 0

    def test_tackle_adds_0_points(self, client, sample_match, db):
        client.post(f"/live/{sample_match.id}/events", data=event_form("tackle", "positive"))
        db.refresh(sample_match)
        assert sample_match.score_own == 0

    def test_score_oob_in_response(self, client, sample_match):
        response = client.post(f"/live/{sample_match.id}/events", data=event_form("try", "scored"))
        assert 'id="score-own"' in response.text
        assert "5" in response.text

    def test_zone_saved(self, client, sample_match, db):
        client.post(f"/live/{sample_match.id}/events", data=event_form("scrum", "won", zone=3))
        event = db.query(Event).filter_by(match_id=sample_match.id).first()
        assert event.zone == 3

    def test_notes_saved(self, client, sample_match, db):
        client.post(f"/live/{sample_match.id}/events", data=event_form("penal", "conceded", notes="off_side"))
        event = db.query(Event).filter_by(match_id=sample_match.id).first()
        assert event.notes == "off_side"

    def test_invalid_match_returns_404(self, client):
        response = client.post("/live/nonexistent/events", data=event_form())
        assert response.status_code == 404

    def test_try_with_conversion_scored_adds_7(self, client, sample_match, db):
        data = event_form("try", "scored")
        data["conversion_attempted"] = "yes"
        data["conversion_result"] = "scored"
        client.post(f"/live/{sample_match.id}/events", data=data)
        db.refresh(sample_match)
        assert sample_match.score_own == 7

    def test_try_with_conversion_missed_adds_5(self, client, sample_match, db):
        data = event_form("try", "scored")
        data["conversion_attempted"] = "yes"
        data["conversion_result"] = "missed"
        client.post(f"/live/{sample_match.id}/events", data=data)
        db.refresh(sample_match)
        assert sample_match.score_own == 5

    def test_try_without_conversion_adds_5(self, client, sample_match, db):
        data = event_form("try", "scored")
        data["conversion_attempted"] = "no"
        client.post(f"/live/{sample_match.id}/events", data=data)
        db.refresh(sample_match)
        assert sample_match.score_own == 5

    def test_try_with_conversion_creates_two_events(self, client, sample_match, db):
        data = event_form("try", "scored")
        data["conversion_attempted"] = "yes"
        data["conversion_result"] = "scored"
        client.post(f"/live/{sample_match.id}/events", data=data)
        events = db.query(Event).filter_by(match_id=sample_match.id).all()
        types = {e.type for e in events}
        assert "try" in types
        assert "conversion" in types
        assert len(events) == 2

    def test_try_without_conversion_creates_one_event(self, client, sample_match, db):
        data = event_form("try", "scored")
        data["conversion_attempted"] = "no"
        client.post(f"/live/{sample_match.id}/events", data=data)
        assert db.query(Event).filter_by(match_id=sample_match.id).count() == 1


class TestPlayerStats:
    def _get_player(self, sample_match, db):
        from models import MatchPlayer
        mp = db.query(MatchPlayer).filter_by(match_id=sample_match.id, number=1).first()
        from models import Player
        return db.query(Player).filter_by(id=mp.player_id).first()

    def _player_id(self, sample_match, db):
        from models import MatchPlayer
        mp = db.query(MatchPlayer).filter_by(match_id=sample_match.id, number=1).first()
        return mp.player_id

    def test_try_increments_tries(self, client, sample_match, db):
        pid = self._player_id(sample_match, db)
        client.post(f"/live/{sample_match.id}/events", data=event_form("try", "scored", player_id=pid))
        player = self._get_player(sample_match, db)
        db.refresh(player)
        assert player.tries == 1

    def test_conversion_scored_increments_attempts_and_scored(self, client, sample_match, db):
        pid = self._player_id(sample_match, db)
        client.post(f"/live/{sample_match.id}/events", data=event_form("conversion", "scored", player_id=pid))
        player = self._get_player(sample_match, db)
        db.refresh(player)
        assert player.conversions_attempts == 1
        assert player.conversions_scored == 1

    def test_conversion_missed_increments_attempts_only(self, client, sample_match, db):
        pid = self._player_id(sample_match, db)
        client.post(f"/live/{sample_match.id}/events", data=event_form("conversion", "missed", player_id=pid))
        player = self._get_player(sample_match, db)
        db.refresh(player)
        assert player.conversions_attempts == 1
        assert player.conversions_scored == 0

    def test_drop_scored_increments_attempts_and_scored(self, client, sample_match, db):
        pid = self._player_id(sample_match, db)
        client.post(f"/live/{sample_match.id}/events", data=event_form("drop", "scored", player_id=pid))
        player = self._get_player(sample_match, db)
        db.refresh(player)
        assert player.drops_attempts == 1
        assert player.drops_scored == 1

    def test_drop_missed_increments_attempts_only(self, client, sample_match, db):
        pid = self._player_id(sample_match, db)
        client.post(f"/live/{sample_match.id}/events", data=event_form("drop", "missed", player_id=pid))
        player = self._get_player(sample_match, db)
        db.refresh(player)
        assert player.drops_attempts == 1
        assert player.drops_scored == 0

    def test_penal_kicked_increments_penals_scored(self, client, sample_match, db):
        pid = self._player_id(sample_match, db)
        client.post(f"/live/{sample_match.id}/events", data=event_form("penal", "kicked", player_id=pid))
        player = self._get_player(sample_match, db)
        db.refresh(player)
        assert player.penals_scored == 1

    def test_penal_conceded_does_not_change_stats(self, client, sample_match, db):
        pid = self._player_id(sample_match, db)
        client.post(f"/live/{sample_match.id}/events", data=event_form("penal", "conceded", player_id=pid))
        player = self._get_player(sample_match, db)
        db.refresh(player)
        assert player.penals_scored == 0

    def test_tackle_positive_updates_tackles(self, client, sample_match, db):
        pid = self._player_id(sample_match, db)
        client.post(f"/live/{sample_match.id}/events", data=event_form("tackle", "positive", player_id=pid))
        player = self._get_player(sample_match, db)
        db.refresh(player)
        assert player.tackles_total == 1
        assert player.tackles_positive == 1
        assert player.tackles_missed == 0

    def test_tackle_missed_updates_tackles(self, client, sample_match, db):
        pid = self._player_id(sample_match, db)
        client.post(f"/live/{sample_match.id}/events", data=event_form("tackle", "missed", player_id=pid))
        player = self._get_player(sample_match, db)
        db.refresh(player)
        assert player.tackles_total == 1
        assert player.tackles_missed == 1
        assert player.tackles_positive == 0

    def test_yellow_card_updates_yellow_cards(self, client, sample_match, db):
        pid = self._player_id(sample_match, db)
        client.post(f"/live/{sample_match.id}/events", data=event_form("tarjeta", "yellow", player_id=pid))
        player = self._get_player(sample_match, db)
        db.refresh(player)
        assert player.yellow_cards == 1

    def test_red_card_updates_red_cards(self, client, sample_match, db):
        pid = self._player_id(sample_match, db)
        client.post(f"/live/{sample_match.id}/events", data=event_form("tarjeta", "red", player_id=pid))
        player = self._get_player(sample_match, db)
        db.refresh(player)
        assert player.red_cards == 1

    def test_try_inline_conversion_updates_kicker_stats(self, client, sample_match, db):
        from models import MatchPlayer
        scorer_mp = db.query(MatchPlayer).filter_by(match_id=sample_match.id, number=1).first()
        kicker_mp = db.query(MatchPlayer).filter_by(match_id=sample_match.id, number=10).first()
        data = event_form("try", "scored", player_id=scorer_mp.player_id)
        data["conversion_attempted"] = "yes"
        data["conversion_result"] = "scored"
        data["conversion_player_id"] = kicker_mp.player_id
        client.post(f"/live/{sample_match.id}/events", data=data)
        from models import Player
        scorer = db.query(Player).filter_by(id=scorer_mp.player_id).first()
        kicker = db.query(Player).filter_by(id=kicker_mp.player_id).first()
        db.refresh(scorer)
        db.refresh(kicker)
        assert scorer.tries == 1
        assert kicker.conversions_scored == 1

    def test_kick_increments_kicks(self, client, sample_match, db):
        pid = self._player_id(sample_match, db)
        client.post(f"/live/{sample_match.id}/events", data=event_form("kick", "recovered", player_id=pid))
        player = self._get_player(sample_match, db)
        db.refresh(player)
        assert player.kicks == 1

    def test_perdida_increments_turnovers(self, client, sample_match, db):
        pid = self._player_id(sample_match, db)
        client.post(f"/live/{sample_match.id}/events", data=event_form("perdida", "knock_on", player_id=pid))
        player = self._get_player(sample_match, db)
        db.refresh(player)
        assert player.turnovers == 1

    def test_lineout_won_increments_lineouts(self, client, sample_match, db):
        pid = self._player_id(sample_match, db)
        client.post(f"/live/{sample_match.id}/events", data=event_form("lineout", "won", player_id=pid))
        player = self._get_player(sample_match, db)
        db.refresh(player)
        assert player.lineouts == 1

    def test_red_card_20min_updates_red_cards_20min(self, client, sample_match, db):
        pid = self._player_id(sample_match, db)
        client.post(f"/live/{sample_match.id}/events", data=event_form("tarjeta", "red_20", player_id=pid))
        player = self._get_player(sample_match, db)
        db.refresh(player)
        assert player.red_cards_20min == 1

    def test_no_player_id_skips_stat_update(self, client, sample_match, db):
        client.post(f"/live/{sample_match.id}/events", data=event_form("try", "scored"))
        from models import Player
        players = db.query(Player).all()
        assert all(p.tries == 0 for p in players)
