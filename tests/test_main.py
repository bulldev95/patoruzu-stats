from database import get_db


def test_root_redirects_to_setup(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (307, 308)
    assert "/setup/" in response.headers["location"]


def test_get_db_yields_session():
    gen = get_db()
    session = next(gen)
    assert session is not None
    try:
        next(gen)
    except StopIteration:
        pass
