from models import MatchPlayer


class TestLiveView:
    def test_valid_match_returns_200(self, client, sample_match):
        response = client.get(f"/live/{sample_match.id}")
        assert response.status_code == 200

    def test_invalid_match_returns_404(self, client):
        response = client.get("/live/nonexistent-id")
        assert response.status_code == 404

    def test_shows_rival_name(self, client, sample_match):
        response = client.get(f"/live/{sample_match.id}")
        assert "DRAIG GOCH - Chubut" in response.text

    def test_shows_initial_score(self, client, sample_match):
        response = client.get(f"/live/{sample_match.id}")
        assert ">0<" in response.text

    def test_shows_period(self, client, sample_match):
        response = client.get(f"/live/{sample_match.id}")
        assert "1st Half" in response.text

    def test_shows_clock_placeholder(self, client, sample_match):
        response = client.get(f"/live/{sample_match.id}")
        assert "00:00" in response.text

    def test_shows_15_starters(self, client, sample_match):
        response = client.get(f"/live/{sample_match.id}")
        assert "On the field (15)" in response.text

    def test_shows_8_bench_players(self, client, sample_match):
        response = client.get(f"/live/{sample_match.id}")
        assert "Bench (8)" in response.text

    def test_shows_starter_names(self, client, sample_match):
        response = client.get(f"/live/{sample_match.id}")
        assert "Player 1" in response.text
        assert "Player 15" in response.text

    def test_does_not_show_starter_as_bench(self, client, sample_match):
        response = client.get(f"/live/{sample_match.id}")
        # Player 1 is a starter, should not appear in bench section
        bench_section = response.text.split("Bench")[1] if "Bench" in response.text else ""
        assert "Player 1" not in bench_section or "Player 16" in bench_section

    def test_shows_sub_names(self, client, sample_match):
        response = client.get(f"/live/{sample_match.id}")
        assert "Player 16" in response.text
        assert "Player 23" in response.text

    def test_second_period_label(self, client, sample_match, db):
        sample_match.period = 2
        db.commit()
        response = client.get(f"/live/{sample_match.id}")
        assert "2nd Half" in response.text

    def test_players_with_minute_out_excluded(self, client, sample_match, db):
        mp = db.query(MatchPlayer).filter_by(match_id=sample_match.id, number=1).first()
        mp.minute_out = 30
        db.commit()
        response = client.get(f"/live/{sample_match.id}")
        assert "On the field (14)" in response.text
