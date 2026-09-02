from app.main import app
from fastapi.testclient import TestClient


def test_live_health_ok():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert "X-Request-ID" in response.headers


def test_index_renders_dis():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "ДИС" in response.text
        assert "кадровые решения" in response.text.lower()


def test_login_page_ok():
    with TestClient(app) as client:
        response = client.get("/login")
        assert response.status_code == 200
        assert "csrf_token" in response.text
