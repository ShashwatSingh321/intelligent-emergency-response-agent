
import pytest

from emergency_response.database.emergency_repository import (
    EmergencyRepository,
)
from emergency_response.models.ambulance import (
    Ambulance,
    AmbulanceStatus,
)
from emergency_response.models.emergency import (
    EmergencyReport,
    EmergencyStatus,
    EmergencyType,
)
from emergency_response.routing.graph import CampusGraph
from emergency_response.services.emergency_workflow import (
    EmergencyWorkflow,
)


def make_report(report_id="ER-WORKFLOW-001"):
    return EmergencyReport(
        id=report_id,
        description="A student needs medical assistance",
        emergency_type=EmergencyType.MEDICAL,
        location_id="LIBRARY",
    )


def make_workflow(tmp_path):
    graph = CampusGraph()
    graph.add_connection("MAIN_GATE", "LIBRARY", 2)

    ambulances = [
        Ambulance(
            id="AMB-01",
            current_location_id="MAIN_GATE",
            status=AmbulanceStatus.AVAILABLE,
            equipment={"first_aid"},
            capacity=2,
        )
    ]

    repository = EmergencyRepository(tmp_path / "reports.json")

    return EmergencyWorkflow(repository, graph, ambulances)


def test_submit_saves_report_and_returns_recommendation(tmp_path):
    workflow = make_workflow(tmp_path)
    report = make_report()

    result = workflow.submit_report(
        report,
        required_equipment={"first_aid"},
    )

    assert result.report_id == report.id
    assert result.ambulance is not None
    assert result.ambulance.id == "AMB-01"
    assert workflow.get_report(report.id) == report


def test_duplicate_report_is_rejected(tmp_path):
    workflow = make_workflow(tmp_path)
    report = make_report()

    workflow.submit_report(report)

    with pytest.raises(ValueError, match="already exists"):
        workflow.submit_report(report)


def test_list_reports_returns_saved_reports(tmp_path):
    workflow = make_workflow(tmp_path)
    first = make_report("ER-001")
    second = make_report("ER-002")

    workflow.submit_report(first)
    workflow.submit_report(second)

    assert workflow.list_reports() == [first, second]


def test_get_missing_report_returns_none(tmp_path):
    workflow = make_workflow(tmp_path)

    assert workflow.get_report("UNKNOWN") is None




def test_unknown_campus_location_is_rejected(tmp_path):
    workflow = make_workflow(tmp_path)
    report = make_report()

    # LIBRARY is valid; this location is not on the campus map.
    report.location_id = "UNKNOWN_LOCATION"

    with pytest.raises(ValueError, match="Unknown campus location"):
        workflow.submit_report(report)


def test_invalid_location_report_is_not_saved(tmp_path):
    workflow = make_workflow(tmp_path)
    report = make_report()

    report.location_id = "UNKNOWN_LOCATION"

    with pytest.raises(ValueError, match="Unknown campus location"):
        workflow.submit_report(report)

    assert workflow.get_report(report.id) is None




def test_workflow_can_transition_report_status(tmp_path):
    workflow = make_workflow(tmp_path)
    report = make_report()

    workflow.submit_report(report)

    updated = workflow.transition_status(
        report.id,
        EmergencyStatus.UNDER_REVIEW,
    )

    assert updated.status == EmergencyStatus.UNDER_REVIEW
    assert workflow.get_report(report.id).status == (
        EmergencyStatus.UNDER_REVIEW
    )


def test_workflow_rejects_invalid_status_transition(tmp_path):
    workflow = make_workflow(tmp_path)
    report = make_report()

    workflow.submit_report(report)

    with pytest.raises(ValueError, match="Cannot transition"):
        workflow.transition_status(
            report.id,
            EmergencyStatus.RESOLVED,
        )

    assert workflow.get_report(report.id).status == (
        EmergencyStatus.REPORTED
    )


def test_workflow_rejects_status_change_for_missing_report(tmp_path):
    workflow = make_workflow(tmp_path)

    with pytest.raises(KeyError, match="Report not found"):
        workflow.transition_status(
            "UNKNOWN-REPORT",
            EmergencyStatus.UNDER_REVIEW,
        )




def test_workflow_returns_route_and_cost_for_recommended_ambulance(tmp_path):
    workflow = make_workflow(tmp_path)

    result = workflow.submit_report(
        make_report(),
        required_equipment={"first_aid"},
    )

    assert result.ambulance is not None
    assert result.route == ["MAIN_GATE", "LIBRARY"]
    assert result.route_cost == 2
    assert result.ambulance_found is True
    assert result.route_found is True


def test_workflow_handles_no_suitable_ambulance(tmp_path):
    workflow = make_workflow(tmp_path)

    workflow.ambulances = []

    result = workflow.submit_report(
        make_report(),
        required_equipment={"first_aid"},
    )

    assert result.ambulance is None
    assert result.route == []
    assert result.route_found is False
    assert "human review" in result.recommendation.lower()


def test_workflow_rejects_ambulance_without_required_equipment(tmp_path):
    workflow = make_workflow(tmp_path)

    workflow.ambulances[0].equipment = set()

    result = workflow.submit_report(
        make_report(),
        required_equipment={"first_aid"},
    )

    assert result.ambulance is None
    assert result.route == []
    assert result.route_found is False


def test_recommendation_does_not_dispatch_ambulance(tmp_path):
    workflow = make_workflow(tmp_path)
    ambulance = workflow.ambulances[0]

    result = workflow.submit_report(
        make_report(),
        required_equipment={"first_aid"},
    )

    assert result.ambulance is ambulance
    assert ambulance.status == AmbulanceStatus.AVAILABLE
    assert workflow.get_report("ER-WORKFLOW-001").status == (
        EmergencyStatus.REPORTED
    )
