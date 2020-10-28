import pytest
from main import create_app


@pytest.fixture
def client():
    app = create_app()
    with app.test_client() as client:
        yield client


def test_mytest(client):
    resp = client.get('/healthz')
    assert resp.status_code == 200


