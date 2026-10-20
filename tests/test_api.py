
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from emergency_response import api as api_module
from emergency_response.database.emergency_repository import (
    EmergencyRepository,
)
from emergency_response.database.repository import (
    load_ambulances,
    load_campus_graph,
)
from emergency_response.models.emergency import (
    EmergencyReport,
    EmergencyStatus,
)
from emergency_response.services.emergency_workflow import (
    EmergencyWorkflow,
)


client = TestClient(api_module.app)


@pytest.fixture
def isolated_workflow(tmp_path, monkeypatch):
    """Give each test its own temporary report and history files."""
    project_root = Path(__file__).resolve().parents[1]
    data_dir = project_root / "data"

    repository = EmergencyRepository(
        tmp_path / "emergency_reports.json"
    )
    graph = load_campus_graph(data_dir / "campus_map.json")
    ambulances = load_ambulances(
        data_dir / "sample_ambulances.json"
    )

    workflow = EmergencyWorkflow(
        repository=repository,
        graph=graph,
        ambulances=ambulances,
    )

    monkeypatch.setattr(
        api_module,
        "get_workflow",
        lambda: workflow,
    )

    return workflow


def test_health_check(isolated_workflow):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_documentation_is_available(isolated_workflow):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/emergencies" in response.json()["paths"]


def test_list_emergencies(isolated_workflow):
    response = client.get("/emergencies")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_unknown_emergency_returns_404(isolated_workflow):
    response = client.get("/emergencies/UNKNOWN-REPORT-ID")

    assert response.status_code == 404


def test_invalid_emergency_request_returns_422(isolated_workflow):
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


def test_create_emergency_successfully(isolated_workflow):
    response = client.post(
        "/emergencies",
        json={
            "description": "A student needs first aid after an injury",
            "emergency_type": "medical",
            "location_id": "MAIN_GATE",
            "people_affected": 1,
        },
    )

    assert response.status_code == 201

    data = response.json()
    assert data["report_id"].startswith("ER-")
    assert data["description"] == (
        "A student needs first aid after an injury"
    )
    assert data["emergency_type"] == "medical"
    assert data["location_id"] == "MAIN_GATE"
    assert data["status"] == "reported"
    assert 1 <= data["priority"] <= 5


def test_unknown_campus_location_returns_400(isolated_workflow):
    response = client.post(
        "/emergencies",
        json={
            "description": "A student needs medical assistance",
            "emergency_type": "medical",
            "location_id": "LOCATION_THAT_DOES_NOT_EXIST",
            "people_affected": 1,
        },
    )

    assert response.status_code == 400
    assert "Unknown campus location" in response.json()["detail"]


def test_status_transition_is_recorded_in_history(
    isolated_workflow,
):
    report_id = "ER-API-HISTORY-TEST"

    report = EmergencyReport(
        id=report_id,
        description="Test report for API status history",
        emergency_type="medical",
        location_id="MAIN_GATE",
    )

    isolated_workflow.repository.save(report)

    updated_report = isolated_workflow.transition_status(
        report_id,
        EmergencyStatus.UNDER_REVIEW,
    )

    assert updated_report.status == EmergencyStatus.UNDER_REVIEW

    history = isolated_workflow.status_service.get_history(report_id)

    assert len(history) == 1
    assert history[0].report_id == report_id
    assert history[0].previous_status == EmergencyStatus.REPORTED
    assert history[0].new_status == EmergencyStatus.UNDER_REVIEW



def test_whitespace_only_description_is_rejected(isolated_workflow):
    response = client.post(
        "/emergencies",
        json={
            "description": "   ",
            "emergency_type": "medical",
            "location_id": "MAIN_GATE",
        },
    )

    assert response.status_code == 422


def test_description_and_location_are_trimmed(isolated_workflow):
    response = client.post(
        "/emergencies",
        json={
            "description": "  A student needs medical assistance  ",
            "emergency_type": "medical",
            "location_id": " MAIN_GATE ",
        },
    )

    assert response.status_code == 201

    data = response.json()
    assert data["description"] == "A student needs medical assistance"
    assert data["location_id"] == "MAIN_GATE"


def test_unexpected_request_field_is_rejected(isolated_workflow):
    response = client.post(
        "/emergencies",
        json={
            "description": "A student needs medical assistance",
            "emergency_type": "medical",
            "location_id": "MAIN_GATE",
            "unexpected_field": "not allowed",
        },
    )

    assert response.status_code == 422
