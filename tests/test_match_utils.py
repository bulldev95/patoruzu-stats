import time
from models import Event, MatchPlayer, Player
from utils.match_utils import calculate_minute, get_active_players, get_recent_events
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
    def test_returns_only_players_without_minute_out(self, db, sample_match):
        # Set minute_out on player #1
        mp = db.query(MatchPlayer).filter_by(match_id=sample_match.id, number=1).first()
        mp.minute_out = 30
        db.commit()

        active = get_active_players(sample_match.id, db)
        numbers = [mp.number for mp, _ in active]
        assert 1 not in numbers
        assert 2 in numbers

    def test_returns_all_when_none_substituted(self, db, sample_match):
        active = get_active_players(sample_match.id, db)
        assert len(active) == 23

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
