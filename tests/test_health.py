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
        assert "Вход" in response.text
        assert "Web-панель для методиста" in response.text
        assert 'name="email"' in response.text
        assert 'name="password"' in response.text
        assert 'autocomplete="username"' in response.text
        assert 'autocomplete="current-password"' in response.text


def test_author_and_footer_on_pages():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert 'name="author" content="Степанов Д.А."' in response.text
        assert "Автор проекта: Степанов Д.А." in response.text
        assert "site-footer" in response.text
        login = client.get("/login")
        assert login.status_code == 200
        assert "Автор проекта: Степанов Д.А." in login.text
        assert "nav-toggle-btn" in login.text
        assert "button-primary" in login.text


def test_static_css_serves_brand_tokens():
    with TestClient(app) as client:
        response = client.get("/static/css/app.css")
        assert response.status_code == 200
        assert "--brand-primary: #4f46e5" in response.text.lower() or "--brand-primary: #4F46E5" in response.text
        assert response.text.count(".container {") == 1
        assert ".button-primary" in response.text
        assert ".button-secondary" in response.text
        assert ".site-footer" in response.text
        assert "#1e3a8a" in response.text.lower()
