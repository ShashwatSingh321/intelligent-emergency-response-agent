
from math import inf

from emergency_response.models.ambulance import (
    Ambulance,
    AmbulanceStatus,
)
from emergency_response.models.emergency import (
    EmergencyReport,
    EmergencyType,
)
from emergency_response.routing.graph import CampusGraph
from emergency_response.services.emergency_service import (
    process_emergency,
)


def make_graph():
    graph = CampusGraph()
    graph.add_connection("MAIN_GATE", "LIBRARY", 2)
    graph.add_connection("HOSTEL", "LIBRARY", 5)
    return graph


def test_process_emergency_recommends_nearest_eligible_ambulance():
    report = EmergencyReport(
        id="ER-TEST-001",
        description="A student has a medical emergency",
        emergency_type=EmergencyType.MEDICAL,
        location_id="LIBRARY",
    )

    ambulances = [
        Ambulance(
            id="AMB-01",
            current_location_id="MAIN_GATE",
            status=AmbulanceStatus.AVAILABLE,
            equipment={"first_aid"},
            capacity=2,
        ),
        Ambulance(
            id="AMB-02",
            current_location_id="HOSTEL",
            status=AmbulanceStatus.AVAILABLE,
            equipment={"first_aid"},
            capacity=2,
        ),
    ]

    result = process_emergency(
        report, ambulances, make_graph(),
        required_equipment={"first_aid"},
    )

    assert result.report_id == "ER-TEST-001"
    assert result.priority == 3
    assert result.ambulance is not None
    assert result.ambulance.id == "AMB-01"
    assert result.route == ["MAIN_GATE", "LIBRARY"]
    assert result.route_cost == 2
    assert result.ambulance_found
    assert result.route_found
    assert report.status.value == "reported"


def test_process_emergency_handles_no_available_ambulance():
    report = EmergencyReport(
        id="ER-TEST-002",
        description="A student needs medical assistance",
        emergency_type=EmergencyType.MEDICAL,
        location_id="LIBRARY",
    )

    ambulances = [
        Ambulance(
            id="AMB-03",
            current_location_id="MAIN_GATE",
            status=AmbulanceStatus.BUSY,
            equipment={"first_aid"},
            capacity=2,
        )
    ]

    result = process_emergency(report, ambulances, make_graph())

    assert result.ambulance is None
    assert result.route == []
    assert result.route_cost == inf
    assert not result.ambulance_found
    assert not result.route_found
    assert "No suitable reachable ambulance" in result.recommendation
