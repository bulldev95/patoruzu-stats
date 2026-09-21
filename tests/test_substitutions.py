from models import MatchPlayer, Player, Substitution


def _player_id(sample_match, db, number):
    return db.query(MatchPlayer).filter_by(match_id=sample_match.id, number=number).first().player_id


class TestSubstitutionSheet:
    def test_sheet_returns_200(self, client, sample_match, db):
        pid = _player_id(sample_match, db, 1)
        response = client.get(f"/live/{sample_match.id}/substitutions/sheet?player_out_id={pid}")
        assert response.status_code == 200

    def test_sheet_shows_player_out(self, client, sample_match, db):
        pid = _player_id(sample_match, db, 1)
        response = client.get(f"/live/{sample_match.id}/substitutions/sheet?player_out_id={pid}")
        assert "Surname1" in response.text

    def test_sheet_shows_bench_players(self, client, sample_match, db):
        pid = _player_id(sample_match, db, 1)
        response = client.get(f"/live/{sample_match.id}/substitutions/sheet?player_out_id={pid}")
        assert "Surname16" in response.text

    def test_sheet_invalid_player_returns_404(self, client, sample_match):
        response = client.get(f"/live/{sample_match.id}/substitutions/sheet?player_out_id=nonexistent")
        assert response.status_code == 404

    def test_sheet_invalid_match_returns_404(self, client, sample_match, db):
        pid = _player_id(sample_match, db, 1)
        response = client.get(f"/live/nonexistent/substitutions/sheet?player_out_id={pid}")
        assert response.status_code == 404


class TestSaveSubstitution:
    def test_creates_substitution_record(self, client, sample_match, db):
        out_id = _player_id(sample_match, db, 1)
        in_id = _player_id(sample_match, db, 16)
        client.post(f"/live/{sample_match.id}/substitutions",
                    data={"player_out_id": out_id, "player_in_id": in_id, "position": "Prop"})
        assert db.query(Substitution).filter_by(match_id=sample_match.id).count() == 1

    def test_sets_minute_out_on_outgoing_player(self, client, sample_match, db):
        out_id = _player_id(sample_match, db, 1)
        in_id = _player_id(sample_match, db, 16)
        client.post(f"/live/{sample_match.id}/substitutions",
                    data={"player_out_id": out_id, "player_in_id": in_id, "position": "Prop"})
        mp_out = db.query(MatchPlayer).filter_by(match_id=sample_match.id, player_id=out_id).first()
        db.refresh(mp_out)
        assert mp_out.minute_out is not None

    def test_sets_minute_in_on_incoming_player(self, client, sample_match, db):
        out_id = _player_id(sample_match, db, 1)
        in_id = _player_id(sample_match, db, 16)
        client.post(f"/live/{sample_match.id}/substitutions",
                    data={"player_out_id": out_id, "player_in_id": in_id, "position": "Prop"})
        mp_in = db.query(MatchPlayer).filter_by(match_id=sample_match.id, player_id=in_id).first()
        db.refresh(mp_in)
        assert mp_in.minute_in is not None

    def test_sets_position_on_incoming_player(self, client, sample_match, db):
        out_id = _player_id(sample_match, db, 1)
        in_id = _player_id(sample_match, db, 16)
        client.post(f"/live/{sample_match.id}/substitutions",
                    data={"player_out_id": out_id, "player_in_id": in_id, "position": "Flanker"})
        mp_in = db.query(MatchPlayer).filter_by(match_id=sample_match.id, player_id=in_id).first()
        db.refresh(mp_in)
        assert mp_in.position == "Flanker"

    def test_substitution_stores_correct_players(self, client, sample_match, db):
        out_id = _player_id(sample_match, db, 1)
        in_id = _player_id(sample_match, db, 16)
        client.post(f"/live/{sample_match.id}/substitutions",
                    data={"player_out_id": out_id, "player_in_id": in_id, "position": "Prop"})
        sub = db.query(Substitution).filter_by(match_id=sample_match.id).first()
        assert sub.player_out_id == out_id
        assert sub.player_in_id == in_id

    def test_returns_on_field_partial(self, client, sample_match, db):
        out_id = _player_id(sample_match, db, 1)
        in_id = _player_id(sample_match, db, 16)
        response = client.post(f"/live/{sample_match.id}/substitutions",
                                data={"player_out_id": out_id, "player_in_id": in_id, "position": "Prop"})
        assert response.status_code == 200
        assert "<html>" not in response.text

    def test_outgoing_player_not_in_response(self, client, sample_match, db):
        out_id = _player_id(sample_match, db, 1)
        in_id = _player_id(sample_match, db, 16)
        response = client.post(f"/live/{sample_match.id}/substitutions",
                                data={"player_out_id": out_id, "player_in_id": in_id, "position": "Prop"})
        assert "Surname16" in response.text

    def test_invalid_player_out_returns_404(self, client, sample_match, db):
        in_id = _player_id(sample_match, db, 16)
        response = client.post(f"/live/{sample_match.id}/substitutions",
                                data={"player_out_id": "nonexistent", "player_in_id": in_id, "position": "Prop"})
        assert response.status_code == 404

    def test_invalid_player_in_returns_404(self, client, sample_match, db):
        out_id = _player_id(sample_match, db, 1)
        response = client.post(f"/live/{sample_match.id}/substitutions",
                                data={"player_out_id": out_id, "player_in_id": "nonexistent", "position": "Prop"})
        assert response.status_code == 404

    def test_invalid_match_returns_404(self, client, sample_match, db):
        out_id = _player_id(sample_match, db, 1)
        in_id = _player_id(sample_match, db, 16)
        response = client.post(f"/live/nonexistent/substitutions",
                                data={"player_out_id": out_id, "player_in_id": in_id, "position": "Prop"})
        assert response.status_code == 404


class TestActivePlayersAfterSubstitution:
    def test_incoming_player_appears_in_active(self, client, sample_match, db):
        from services.match_utils import get_active_players
        out_id = _player_id(sample_match, db, 1)
        in_id = _player_id(sample_match, db, 16)
        client.post(f"/live/{sample_match.id}/substitutions",
                    data={"player_out_id": out_id, "player_in_id": in_id, "position": "Prop"})
        active_ids = [p.id for _, p in get_active_players(sample_match.id, db)]
        assert in_id in active_ids

    def test_outgoing_player_not_in_active(self, client, sample_match, db):
        from services.match_utils import get_active_players
        out_id = _player_id(sample_match, db, 1)
        in_id = _player_id(sample_match, db, 16)
        client.post(f"/live/{sample_match.id}/substitutions",
                    data={"player_out_id": out_id, "player_in_id": in_id, "position": "Prop"})
        active_ids = [p.id for _, p in get_active_players(sample_match.id, db)]
        assert out_id not in active_ids

    def test_active_count_unchanged_after_substitution(self, client, sample_match, db):
        from services.match_utils import get_active_players
        before = len(get_active_players(sample_match.id, db))
        out_id = _player_id(sample_match, db, 1)
        in_id = _player_id(sample_match, db, 16)
        client.post(f"/live/{sample_match.id}/substitutions",
                    data={"player_out_id": out_id, "player_in_id": in_id, "position": "Prop"})
        after = len(get_active_players(sample_match.id, db))
        assert after == before
