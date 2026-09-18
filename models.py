import uuid
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from database import Base


def new_id():
    return str(uuid.uuid4())


class Player(Base):
    __tablename__ = "players"

    id = Column(String, primary_key=True, default=new_id)
    name = Column(String, nullable=False)

    # Totales históricos
    games_played = Column(Integer, default=0)
    minutes_played = Column(Integer, default=0)
    tries = Column(Integer, default=0)
    conversions_attempts = Column(Integer, default=0)
    conversions_scored = Column(Integer, default=0)
    drops_attempts = Column(Integer, default=0)
    drops_scored = Column(Integer, default=0)
    tackles_total = Column(Integer, default=0)
    tackles_positive = Column(Integer, default=0)
    tackles_missed = Column(Integer, default=0)
    kicks = Column(Integer, default=0)
    turnovers = Column(Integer, default=0)
    lineouts = Column(Integer, default=0)
    yellow_cards = Column(Integer, default=0)
    red_cards = Column(Integer, default=0)
    red_cards_20min = Column(Integer, default=0)


class Match(Base):
    __tablename__ = "matches"

    id = Column(String, primary_key=True, default=new_id)
    date = Column(String, nullable=False)
    rival = Column(String, nullable=False)
    competition = Column(String, nullable=False)
    venue = Column(String, nullable=True)

    # Marcador
    score_own = Column(Integer, default=0)
    score_rival = Column(Integer, default=0)

    # Reloj
    period = Column(Integer, default=1)
    start_timestamp = Column(Float, nullable=True)
    accumulated_time = Column(Integer, default=0)  # milisegundos acumulados

    status = Column(String, default="setup")  # setup / live / paused / finished

    players = relationship("MatchPlayer", back_populates="match")
    events = relationship("Event", back_populates="match")
    substitutions = relationship("Substitution", back_populates="match")


class MatchPlayer(Base):
    __tablename__ = "match_players"

    id = Column(String, primary_key=True, default=new_id)
    match_id = Column(String, ForeignKey("matches.id"), nullable=False)
    player_id = Column(String, ForeignKey("players.id"), nullable=False)
    number = Column(Integer, nullable=False)        # 1–23
    position = Column(String, nullable=True)        # null hasta que ingresa (suplentes)
    is_starter = Column(Boolean, default=False)
    minute_in = Column(Integer, default=0)
    minute_out = Column(Integer, nullable=True)

    match = relationship("Match", back_populates="players")
    player = relationship("Player")


class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, default=new_id)
    match_id = Column(String, ForeignKey("matches.id"), nullable=False)
    minute = Column(Integer, nullable=False)
    period = Column(Integer, nullable=False)
    team = Column(String, nullable=False)           # own / rival
    type = Column(String, nullable=False)           # tackle, try, scrum, etc.
    result = Column(String, nullable=False)
    zone = Column(Integer, nullable=True)           # 1–5
    player_id = Column(String, ForeignKey("players.id"), nullable=True)
    notes = Column(String, nullable=True)

    match = relationship("Match", back_populates="events")
    player = relationship("Player")


class Substitution(Base):
    __tablename__ = "substitutions"

    id = Column(String, primary_key=True, default=new_id)
    match_id = Column(String, ForeignKey("matches.id"), nullable=False)
    minute = Column(Integer, nullable=False)
    player_out_id = Column(String, ForeignKey("players.id"), nullable=False)
    player_in_id = Column(String, ForeignKey("players.id"), nullable=False)
    position = Column(String, nullable=False)

    match = relationship("Match", back_populates="substitutions")
    player_out = relationship("Player", foreign_keys=[player_out_id])
    player_in = relationship("Player", foreign_keys=[player_in_id])
