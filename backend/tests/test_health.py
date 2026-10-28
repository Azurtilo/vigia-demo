from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_json_responses_declare_utf8():
    ok = client.get("/health")
    error = client.get("/no-existe")

    assert ok.headers["content-type"] == "application/json; charset=utf-8"
    assert error.headers["content-type"] == "application/json; charset=utf-8"


def test_openapi_docs_available():
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "VIGIA API"
