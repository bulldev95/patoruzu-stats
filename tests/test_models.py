import uuid
import pytest
from sqlalchemy.exc import IntegrityError

from models import Event, Match, MatchPlayer, Player, Substitution, new_id


def test_new_id_returns_string():
    result = new_id()
    assert isinstance(result, str)
    uuid.UUID(result)  # raises if not a valid UUID


def test_new_id_is_unique():
    assert new_id() != new_id()


class TestPlayer:
    def test_create(self, db):
        player = Player(personal_id="12345678", name="Roldan, Denis")
        db.add(player)
        db.commit()
        saved = db.query(Player).filter_by(personal_id="12345678").first()
        assert saved.name == "Roldan, Denis"

    def test_id_auto_generated(self, db):
        player = Player(personal_id="11111111", name="Test Player")
        db.add(player)
        db.commit()
        assert player.id is not None
        uuid.UUID(player.id)

    def test_stats_default_to_zero(self, db):
        player = Player(personal_id="22222222", name="Test Player")
        db.add(player)
        db.commit()
        assert player.games_played == 0
        assert player.minutes_played == 0
        assert player.tries == 0
        assert player.conversions_attempts == 0
        assert player.conversions_scored == 0
        assert player.drops_attempts == 0
        assert player.drops_scored == 0
        assert player.tackles_total == 0
        assert player.tackles_positive == 0
        assert player.tackles_missed == 0
        assert player.kicks == 0
        assert player.turnovers == 0
        assert player.lineouts == 0
        assert player.yellow_cards == 0
        assert player.red_cards == 0
        assert player.red_cards_20min == 0

    def test_personal_id_unique_constraint(self, db):
        db.add(Player(personal_id="99999999", name="Player A"))
        db.commit()
        db.add(Player(personal_id="99999999", name="Player B"))
        with pytest.raises(IntegrityError):
            db.commit()

    def test_name_required(self, db):
        db.add(Player(personal_id="88888888", name=None))
        with pytest.raises(IntegrityError):
            db.commit()


class TestMatch:
    def test_create(self, db):
        match = Match(date="2026-08-15", rival="DRAIG GOCH", competition="Torneo Austral")
        db.add(match)
        db.commit()
        saved = db.query(Match).first()
        assert saved.rival == "DRAIG GOCH"

    def test_id_auto_generated(self, db):
        match = Match(date="2026-08-15", rival="DRAIG GOCH", competition="Torneo Austral")
        db.add(match)
        db.commit()
        assert match.id is not None
        uuid.UUID(match.id)

    def test_defaults(self, db):
        match = Match(date="2026-08-15", rival="DRAIG GOCH", competition="Torneo Austral")
        db.add(match)
        db.commit()
        assert match.score_own == 0
        assert match.score_rival == 0
        assert match.period == 1
        assert match.status == "setup"
        assert match.start_timestamp is None
        assert match.accumulated_time == 0
        assert match.venue is None

    def test_venue_optional(self, db):
        match = Match(date="2026-08-15", rival="DRAIG GOCH", competition="Torneo Austral", venue="Cancha Norte")
        db.add(match)
        db.commit()
        assert match.venue == "Cancha Norte"


class TestMatchPlayer:
    def test_create(self, db):
        player = Player(personal_id="33333333", name="Test Player")
        db.add(player)
        match = Match(date="2026-08-15", rival="DRAIG GOCH", competition="Torneo Austral")
        db.add(match)
        db.flush()

        mp = MatchPlayer(
            match_id=match.id,
            player_id=player.id,
            number=1,
            position="Prop",
            is_starter=True,
            minute_in=0,
        )
        db.add(mp)
        db.commit()
        assert mp.minute_out is None
        assert mp.is_starter is True

    def test_sub_has_no_position(self, db):
        player = Player(personal_id="44444444", name="Sub Player")
        db.add(player)
        match = Match(date="2026-08-15", rival="DRAIG GOCH", competition="Torneo Austral")
        db.add(match)
        db.flush()

        mp = MatchPlayer(
            match_id=match.id,
            player_id=player.id,
            number=16,
            position=None,
            is_starter=False,
            minute_in=0,
        )
        db.add(mp)
        db.commit()
        assert mp.position is None


class TestEvent:
    def test_create(self, db):
        player = Player(personal_id="55555555", name="Test Player")
        db.add(player)
        match = Match(date="2026-08-15", rival="DRAIG GOCH", competition="Torneo Austral")
        db.add(match)
        db.flush()

        event = Event(
            match_id=match.id,
            minute=23,
            period=1,
            team="own",
            type="tackle",
            result="positive",
            zone=3,
            player_id=player.id,
        )
        db.add(event)
        db.commit()
        saved = db.query(Event).first()
        assert saved.minute == 23
        assert saved.zone == 3
        assert saved.notes is None

    def test_optional_fields_nullable(self, db):
        match = Match(date="2026-08-15", rival="DRAIG GOCH", competition="Torneo Austral")
        db.add(match)
        db.flush()

        event = Event(
            match_id=match.id,
            minute=5,
            period=1,
            team="rival",
            type="scrum",
            result="lost",
        )
        db.add(event)
        db.commit()
        assert event.zone is None
        assert event.player_id is None
        assert event.notes is None


class TestSubstitution:
    def test_create(self, db):
        player_out = Player(personal_id="66666666", name="Player Out")
        player_in = Player(personal_id="77777777", name="Player In")
        db.add_all([player_out, player_in])
        match = Match(date="2026-08-15", rival="DRAIG GOCH", competition="Torneo Austral")
        db.add(match)
        db.flush()

        sub = Substitution(
            match_id=match.id,
            minute=55,
            player_out_id=player_out.id,
            player_in_id=player_in.id,
            position="Prop",
        )
        db.add(sub)
        db.commit()
        saved = db.query(Substitution).first()
        assert saved.minute == 55
        assert saved.position == "Prop"
        assert saved.player_out.name == "Player Out"
        assert saved.player_in.name == "Player In"
