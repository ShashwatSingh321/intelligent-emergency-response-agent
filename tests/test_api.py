
from fastapi.testclient import TestClient

from emergency_response.api import app, get_workflow


client = TestClient(app)


def setup_function():
    get_workflow.cache_clear()


def teardown_function():
    get_workflow.cache_clear()


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_documentation_is_available():
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/emergencies" in response.json()["paths"]


def test_list_emergencies():
    response = client.get("/emergencies")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_unknown_emergency_returns_404():
    response = client.get("/emergencies/UNKNOWN-REPORT-ID")

    assert response.status_code == 404


def test_invalid_emergency_request_returns_422():
    response = client.post(
        "/emergencies",
        json={
            "description": "x",
            "emergency_type": "medical",
            "location_id": "MAIN_GATE",
            "people_affected": 1,
        },
    )

    assert response.status_code == 422
