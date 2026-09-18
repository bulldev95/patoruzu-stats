from unittest.mock import patch

from models import Match, MatchPlayer, Player
from tests.conftest import SAMPLE_PLAYERS, confirm_form_data

PARSED_DATA = {
    "date": "2026-08-15",
    "rival": "DRAIG GOCH - Chubut",
    "competition": "Torneo Austral 2026 (Primera División)",
    "venue": "DRAIG GOCH - Chubut",
    "players": SAMPLE_PLAYERS,
}


class TestSetupPage:
    def test_get_returns_200(self, client):
        response = client.get("/setup/")
        assert response.status_code == 200

    def test_get_contains_file_input(self, client):
        response = client.get("/setup/")
        assert 'type="file"' in response.text

    def test_get_contains_upload_action(self, client):
        response = client.get("/setup/")
        assert "/setup/upload" in response.text


class TestUploadPDF:
    def test_upload_returns_200(self, client):
        with patch("routers.setup.parse_team_sheet", return_value=PARSED_DATA):
            response = client.post(
                "/setup/upload",
                files={"file": ("teams.pdf", b"%PDF fake content", "application/pdf")},
            )
        assert response.status_code == 200

    def test_upload_shows_extracted_date(self, client):
        with patch("routers.setup.parse_team_sheet", return_value=PARSED_DATA):
            response = client.post(
                "/setup/upload",
                files={"file": ("teams.pdf", b"%PDF fake content", "application/pdf")},
            )
        assert "2026-08-15" in response.text

    def test_upload_shows_rival(self, client):
        with patch("routers.setup.parse_team_sheet", return_value=PARSED_DATA):
            response = client.post(
                "/setup/upload",
                files={"file": ("teams.pdf", b"%PDF fake content", "application/pdf")},
            )
        assert "DRAIG GOCH - Chubut" in response.text

    def test_upload_shows_competition(self, client):
        with patch("routers.setup.parse_team_sheet", return_value=PARSED_DATA):
            response = client.post(
                "/setup/upload",
                files={"file": ("teams.pdf", b"%PDF fake content", "application/pdf")},
            )
        assert "Torneo Austral 2026" in response.text

    def test_upload_shows_player_names(self, client):
        with patch("routers.setup.parse_team_sheet", return_value=PARSED_DATA):
            response = client.post(
                "/setup/upload",
                files={"file": ("teams.pdf", b"%PDF fake content", "application/pdf")},
            )
        assert "Player 1" in response.text
        assert "Player 15" in response.text
        assert "Player 23" in response.text

    def test_upload_shows_personal_ids(self, client):
        with patch("routers.setup.parse_team_sheet", return_value=PARSED_DATA):
            response = client.post(
                "/setup/upload",
                files={"file": ("teams.pdf", b"%PDF fake content", "application/pdf")},
            )
        assert SAMPLE_PLAYERS[0]["personal_id"] in response.text

    def test_upload_contains_confirm_action(self, client):
        with patch("routers.setup.parse_team_sheet", return_value=PARSED_DATA):
            response = client.post(
                "/setup/upload",
                files={"file": ("teams.pdf", b"%PDF fake content", "application/pdf")},
            )
        assert "/setup/confirm" in response.text


class TestConfirmSetup:
    def test_confirm_redirects(self, client):
        response = client.post("/setup/confirm", data=confirm_form_data(), follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"].startswith("/live/")

    def test_confirm_creates_match(self, client, db):
        client.post("/setup/confirm", data=confirm_form_data())
        assert db.query(Match).count() == 1

    def test_confirm_match_data(self, client, db):
        client.post("/setup/confirm", data=confirm_form_data())
        match = db.query(Match).first()
        assert match.date == "2026-08-15"
        assert match.rival == "DRAIG GOCH - Chubut"
        assert match.competition == "Torneo Austral 2026 (Primera División)"
        assert match.venue == "DRAIG GOCH - Chubut"
        assert match.status == "setup"

    def test_confirm_creates_23_players(self, client, db):
        client.post("/setup/confirm", data=confirm_form_data())
        assert db.query(Player).count() == 23

    def test_confirm_players_have_personal_id(self, client, db):
        client.post("/setup/confirm", data=confirm_form_data())
        player = db.query(Player).filter_by(personal_id=SAMPLE_PLAYERS[0]["personal_id"]).first()
        assert player is not None

    def test_confirm_creates_23_match_players(self, client, db):
        client.post("/setup/confirm", data=confirm_form_data())
        assert db.query(MatchPlayer).count() == 23

    def test_confirm_starters_have_position(self, client, db):
        client.post("/setup/confirm", data=confirm_form_data())
        starters = db.query(MatchPlayer).filter(MatchPlayer.is_starter == True).all()
        assert len(starters) == 15
        for mp in starters:
            assert mp.position is not None

    def test_confirm_subs_have_no_position(self, client, db):
        client.post("/setup/confirm", data=confirm_form_data())
        subs = db.query(MatchPlayer).filter(MatchPlayer.is_starter == False).all()
        assert len(subs) == 8
        for mp in subs:
            assert mp.position is None

    def test_confirm_starters_minute_in_zero(self, client, db):
        client.post("/setup/confirm", data=confirm_form_data())
        for mp in db.query(MatchPlayer).all():
            assert mp.minute_in == 0
            assert mp.minute_out is None

    def test_confirm_existing_player_not_duplicated(self, client, db):
        existing = Player(personal_id=SAMPLE_PLAYERS[0]["personal_id"], name="Old Name")
        db.add(existing)
        db.commit()

        client.post("/setup/confirm", data=confirm_form_data())

        count = db.query(Player).filter_by(personal_id=SAMPLE_PLAYERS[0]["personal_id"]).count()
        assert count == 1

    def test_confirm_existing_player_name_updated(self, client, db):
        existing = Player(personal_id=SAMPLE_PLAYERS[0]["personal_id"], name="Old Name")
        db.add(existing)
        db.commit()

        client.post("/setup/confirm", data=confirm_form_data())

        player = db.query(Player).filter_by(personal_id=SAMPLE_PLAYERS[0]["personal_id"]).first()
        assert player.name == SAMPLE_PLAYERS[0]["name"]

    def test_confirm_venue_optional(self, client, db):
        data = confirm_form_data(venue="")
        client.post("/setup/confirm", data=data)
        match = db.query(Match).first()
        assert match.venue is None

    def test_confirm_redirect_location_contains_match_id(self, client, db):
        response = client.post("/setup/confirm", data=confirm_form_data(), follow_redirects=False)
        match = db.query(Match).first()
        assert match.id in response.headers["location"]
