import time
from models import Event, MatchPlayer, Player
from services.match_utils import get_active_players, get_recent_events
from utils.match_utils import accumulate_player_stat, accumulate_team_stat, calculate_minute
from tests.conftest import SAMPLE_PLAYERS, POSITIONS
import uuid


def make_match(db, **kwargs):
    from models import Match
    m = Match(
        id=str(uuid.uuid4()),
        date="2026-08-15",
        rival="DRAIG GOCH",
        competition="Torneo Austral",
        **kwargs,
    )
    db.add(m)
    db.flush()
    return m


class TestCalculateMinute:
    def test_returns_zero_when_not_started(self, db):
        match = make_match(db, accumulated_time=0, start_timestamp=None)
        assert calculate_minute(match) == 0

    def test_returns_accumulated_when_paused(self, db):
        match = make_match(db, accumulated_time=120000, start_timestamp=None)
        assert calculate_minute(match) == 2  # 120000ms = 2 minutes

    def test_counts_elapsed_when_running(self, db):
        ts = int(time.time() * 1000) - 65000  # started 65 seconds ago
        match = make_match(db, accumulated_time=0, start_timestamp=ts)
        assert calculate_minute(match) == 1  # 65s = 1 minute

    def test_adds_accumulated_to_elapsed(self, db):
        ts = int(time.time() * 1000) - 61000  # 61s elapsed since resume
        match = make_match(db, accumulated_time=2400000, start_timestamp=ts)  # 40min + 61s
        assert calculate_minute(match) == 41

    def test_never_negative(self, db):
        match = make_match(db, accumulated_time=0, start_timestamp=None)
        assert calculate_minute(match) >= 0


class TestGetActivePlayers:
    def test_excludes_starters_with_minute_out(self, db, sample_match):
        mp = db.query(MatchPlayer).filter_by(match_id=sample_match.id, number=1).first()
        mp.minute_out = 30
        db.commit()

        active = get_active_players(sample_match.id, db)
        numbers = [mp.number for mp, _ in active]
        assert 1 not in numbers
        assert 2 in numbers

    def test_excludes_bench_players(self, db, sample_match):
        active = get_active_players(sample_match.id, db)
        numbers = [mp.number for mp, _ in active]
        assert all(n <= 15 for n in numbers)

    def test_returns_only_starters_initially(self, db, sample_match):
        active = get_active_players(sample_match.id, db)
        assert len(active) == 15

    def test_ordered_by_number(self, db, sample_match):
        active = get_active_players(sample_match.id, db)
        numbers = [mp.number for mp, _ in active]
        assert numbers == sorted(numbers)

    def test_returns_player_objects(self, db, sample_match):
        active = get_active_players(sample_match.id, db)
        mp, player = active[0]
        assert hasattr(player, "surname")
        assert hasattr(mp, "number")


class TestGetRecentEvents:
    def _add_event(self, db, match_id, minute, event_type="tackle"):
        e = Event(
            match_id=match_id, minute=minute, period=1,
            team="own", type=event_type, result="positive",
        )
        db.add(e)
        db.flush()
        return e

    def test_returns_empty_when_no_events(self, db, sample_match):
        events = get_recent_events(sample_match.id, db)
        assert events == []

    def test_returns_events_for_match(self, db, sample_match):
        self._add_event(db, sample_match.id, 5)
        db.commit()
        events = get_recent_events(sample_match.id, db)
        assert len(events) == 1

    def test_default_limit_is_10(self, db, sample_match):
        for i in range(15):
            self._add_event(db, sample_match.id, i)
        db.commit()
        events = get_recent_events(sample_match.id, db)
        assert len(events) == 10

    def test_custom_limit(self, db, sample_match):
        for i in range(5):
            self._add_event(db, sample_match.id, i)
        db.commit()
        events = get_recent_events(sample_match.id, db, limit=3)
        assert len(events) == 3

    def test_ordered_most_recent_first(self, db, sample_match):
        e1 = self._add_event(db, sample_match.id, 5)
        e2 = self._add_event(db, sample_match.id, 10)
        db.commit()
        events = get_recent_events(sample_match.id, db)
        assert events[0].id == e2.id
        assert events[1].id == e1.id


class TestAccumulatePlayerStat:
    def _s(self, event_type, result):
        stats = {}
        accumulate_player_stat(stats, event_type, result)
        return stats

    def test_try(self):
        assert self._s("try", "scored") == {"tries": 1}

    def test_conversion_missed(self):
        assert self._s("conversion", "missed") == {"conversions_attempts": 1}

    def test_conversion_scored(self):
        assert self._s("conversion", "scored") == {"conversions_attempts": 1, "conversions_scored": 1}

    def test_drop_missed(self):
        assert self._s("drop", "missed") == {"drops_attempts": 1}

    def test_drop_scored(self):
        assert self._s("drop", "scored") == {"drops_attempts": 1, "drops_scored": 1}

    def test_penal_kicked(self):
        assert self._s("penal", "kicked") == {"penals_scored": 1}

    def test_penal_missed(self):
        assert self._s("penal", "missed") == {}

    def test_tackle_positive(self):
        assert self._s("tackle", "positive") == {"tackles_total": 1, "tackles_positive": 1}

    def test_tackle_negative(self):
        assert self._s("tackle", "negative") == {"tackles_total": 1, "tackles_negative": 1}

    def test_tackle_missed(self):
        assert self._s("tackle", "missed") == {"tackles_total": 1, "tackles_missed": 1}

    def test_tarjeta_yellow(self):
        assert self._s("tarjeta", "yellow") == {"yellow_cards": 1}

    def test_tarjeta_red(self):
        assert self._s("tarjeta", "red") == {"red_cards": 1}

    def test_tarjeta_red_20(self):
        assert self._s("tarjeta", "red_20") == {"red_cards_20min": 1}

    def test_kick(self):
        assert self._s("kick", "any") == {"kicks": 1}

    def test_perdida(self):
        assert self._s("perdida", "any") == {"turnovers": 1}

    def test_team_events_ignored(self):
        assert self._s("scrum", "won") == {}
        assert self._s("lineout", "won") == {}
        assert self._s("ruck", "won") == {}
        assert self._s("maul", "won") == {}

    def test_accumulates_multiple_calls(self):
        stats = {}
        accumulate_player_stat(stats, "try", "scored")
        accumulate_player_stat(stats, "try", "scored")
        assert stats == {"tries": 2}

    def test_unknown_event_type_ignored(self):
        stats = {}
        accumulate_player_stat(stats, "salida", "any")
        accumulate_player_stat(stats, "unknown", "any")
        assert stats == {}


class TestAccumulateTeamStat:
    def _s(self, event_type, result):
        stats = {}
        accumulate_team_stat(stats, event_type, result)
        return stats

    def test_scrum_won(self):
        assert self._s("scrum", "won") == {"scrums": 1, "scrums_won": 1}

    def test_scrum_lost(self):
        assert self._s("scrum", "lost") == {"scrums": 1}

    def test_lineout_won(self):
        assert self._s("lineout", "won") == {"lineouts": 1, "lineouts_won": 1}

    def test_lineout_stolen(self):
        assert self._s("lineout", "stolen") == {"lineouts": 1, "lineouts_won": 1}

    def test_lineout_lost(self):
        assert self._s("lineout", "lost") == {"lineouts": 1}

    def test_ruck_won(self):
        assert self._s("ruck", "won") == {"rucks": 1, "rucks_won": 1}

    def test_ruck_lost(self):
        assert self._s("ruck", "lost") == {"rucks": 1}

    def test_maul_won(self):
        assert self._s("maul", "won") == {"mauls": 1, "mauls_won": 1}

    def test_maul_lost(self):
        assert self._s("maul", "lost") == {"mauls": 1}

    def test_player_events_ignored(self):
        assert self._s("try", "scored") == {}
        assert self._s("tackle", "positive") == {}
        assert self._s("tarjeta", "yellow") == {}

    def test_accumulates_multiple_calls(self):
        stats = {}
        accumulate_team_stat(stats, "scrum", "won")
        accumulate_team_stat(stats, "scrum", "lost")
        assert stats == {"scrums": 2, "scrums_won": 1}

    def test_unknown_event_type_ignored(self):
        stats = {}
        accumulate_team_stat(stats, "salida", "any")
        accumulate_team_stat(stats, "unknown", "any")
        assert stats == {}
