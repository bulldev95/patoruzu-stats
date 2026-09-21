import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from models import Match, MatchPlayer, Player

POSITIONS = {
    1: "Prop", 2: "Hooker", 3: "Prop",
    4: "Lock", 5: "Lock",
    6: "Flanker", 7: "Flanker", 8: "Number 8",
    9: "Scrum-half", 10: "Fly-half",
    11: "Wing", 12: "Centre", 13: "Centre", 14: "Wing", 15: "Fullback",
}

SAMPLE_PLAYERS = [
    {"number": i, "surname": f"Surname{i}", "name": f"Name{i}", "personal_id": f"1000000{i:02d}"}
    for i in range(1, 24)
]

SAMPLE_PDF_TEXT = """\
Planilla de equipo VISITANTE para el partido N°: 320117
Cancha Dia Hora Torneo División Instancia Fecha
DRAIG GOCH - Chubut 2026-08-15 15:30 Torneo Austral 2026 (Primera División) Primera División Fase Regular Fecha 1
Local Puntos Visitante Puntos
DRAIG GOCH - Chubut PATORUZU R.C. - Chubut
Indicar los minutos en los que se producen las incidencias
Información Tarjeta amarilla 1 Tarjeta amarilla 2
Pos Dor 1L O.M. Apellido y Nombre N°Doc Sal. Ent. S.C. L.I. J.G. J.S. DI. S.C. L.I. J.G. J.S. DI. Exp. C.C.
01 1 Roldan, Denis 38797877
02 2 Barrera, Matias 40739351
03 3 Ramos, Gonzalo Lucas 32673813
04 4 Portillo, Lucas 38800875
05 5 Apraiz, Victor 34275817
06 6 Murillo Del Prado, Tomas 45166047
07 7 Bellido, Atilio 38803464
08 8 Achigar, Lucas 38097115
09 9 Ortiz Imaz, Julian 42969926
10 10 Cardoso, Javier 42969716
11 11 San Martin, Enzo 42020018
12 12 Fernandez Marauda, Lucas 37550810
13 13 Keller, Tomas 40384447
14 14 Velazquez, Juan 45380869
15 15 Lanus Coto, Manuel 37559889
16 16 Apraiz, Alan Erik 38784557
17 17 Salmeri, Agustin 28482300
18 18 Striglio, Lautaro 46982307
19 19 Chludil, Alexis 45251665
20 20 Aguilar Vernetti, Geronimo 48684738
21 21 Gri`ths, Tomas 43825945
22 22 Ortega, Nector Ezequiel 39441178
23 23 Lanus Williams, Agustin 32801274
Firma Capitán Local Firma Encargado Local Firma Capitán Visitante Firma Encargado Visitante\
"""

SAMPLE_PDF_TEXT_LOCAL = """\
Planilla de equipo LOCAL para el partido N°: 320118
Cancha Dia Hora Torneo División Instancia Fecha
PATORUZU R.C. - Chubut 2026-09-01 16:00 Torneo Austral 2026 (Primera División) Primera División Fase Regular Fecha 2
Local Puntos Visitante Puntos
PATORUZU R.C. - Chubut OTRO CLUB - Chubut
Indicar los minutos en los que se producen las incidencias
Información Tarjeta amarilla 1 Tarjeta amarilla 2
Pos Dor 1L O.M. Apellido y Nombre N°Doc Sal. Ent. S.C. L.I. J.G. J.S. DI. S.C. L.I. J.G. J.S. DI. Exp. C.C.
01 1 Roldan, Denis 38797877
02 2 Barrera, Matias 40739351
03 3 Ramos, Gonzalo Lucas 32673813
04 4 Portillo, Lucas 38800875
05 5 Apraiz, Victor 34275817
06 6 Murillo Del Prado, Tomas 45166047
07 7 Bellido, Atilio 38803464
08 8 Achigar, Lucas 38097115
09 9 Ortiz Imaz, Julian 42969926
10 10 Cardoso, Javier 42969716
11 11 San Martin, Enzo 42020018
12 12 Fernandez Marauda, Lucas 37550810
13 13 Keller, Tomas 40384447
14 14 Velazquez, Juan 45380869
15 15 Lanus Coto, Manuel 37559889
16 16 Apraiz, Alan Erik 38784557
17 17 Salmeri, Agustin 28482300
18 18 Striglio, Lautaro 46982307
19 19 Chludil, Alexis 45251665
20 20 Aguilar Vernetti, Geronimo 48684738
21 21 Gri`ths, Tomas 43825945
22 22 Ortega, Nector Ezequiel 39441178
23 23 Lanus Williams, Agustin 32801274
Firma Capitán Local Firma Encargado Local Firma Capitán Visitante Firma Encargado Visitante\
"""


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # single shared connection — required for in-memory SQLite
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_match(db):
    match = Match(
        id=str(uuid.uuid4()),
        date="2026-08-15",
        rival="DRAIG GOCH - Chubut",
        competition="Torneo Austral 2026 (Primera División)",
        venue="DRAIG GOCH - Chubut",
    )
    db.add(match)
    db.flush()

    for data in SAMPLE_PLAYERS:
        player = Player(personal_id=data["personal_id"], surname=data["surname"], name=data["name"])
        db.add(player)
        db.flush()
        number = data["number"]
        mp = MatchPlayer(
            match_id=match.id,
            player_id=player.id,
            number=number,
            position=POSITIONS.get(number) if number <= 15 else None,
            is_starter=number <= 15,
            minute_in=0 if number <= 15 else -1,
        )
        db.add(mp)

    db.commit()
    return match


def confirm_form_data(players=None, **overrides):
    players = players or SAMPLE_PLAYERS
    data = {
        "date": "2026-08-15",
        "rival": "DRAIG GOCH - Chubut",
        "competition": "Torneo Austral 2026 (Primera División)",
        "venue": "DRAIG GOCH - Chubut",
        **overrides,
    }
    for i, p in enumerate(players, 1):
        data[f"number_{i}"] = str(p["number"])
        data[f"surname_{i}"] = p["surname"]
        data[f"name_{i}"] = p["name"]
        data[f"personal_id_{i}"] = p["personal_id"]
    return data
