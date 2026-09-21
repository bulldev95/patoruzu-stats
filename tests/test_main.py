from database import get_db


def test_root_returns_homepage(client):
    response = client.get("/")
    assert response.status_code == 200


def test_get_db_yields_session():
    gen = get_db()
    session = next(gen)
    assert session is not None
    try:
        next(gen)
    except StopIteration:
        pass
