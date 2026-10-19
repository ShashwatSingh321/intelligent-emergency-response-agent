
from emergency_response.models.ambulance import Ambulance, AmbulanceStatus
from emergency_response.models.emergency import EmergencyReport
from emergency_response.services.ambulance_service import select_ambulance


def make_report(people_affected=1):
    return EmergencyReport(
        id="ER-201",
        description="A student needs medical assistance",
        location_id="LIBRARY",
        people_affected=people_affected,
    )


def test_selects_available_ambulance_with_required_equipment():
    ambulances = [
        Ambulance(
            id="AMB-01",
            current_location_id="HOSTEL",
            equipment={"first_aid"},
        ),
        Ambulance(
            id="AMB-02",
            current_location_id="LIBRARY",
            equipment={"first_aid", "oxygen"},
        ),
    ]

    selected = select_ambulance(
        make_report(),
        ambulances,
        required_equipment={"first_aid"},
    )

    assert selected is not None
    assert selected.id == "AMB-01"


def test_does_not_select_busy_ambulance():
    ambulances = [
        Ambulance(
            id="AMB-01",
            current_location_id="HOSTEL",
            status=AmbulanceStatus.BUSY,
            equipment={"first_aid"},
        )
    ]

    assert select_ambulance(
        make_report(), ambulances, {"first_aid"}
    ) is None


def test_does_not_select_ambulance_missing_required_equipment():
    ambulances = [
        Ambulance(
            id="AMB-01",
            current_location_id="HOSTEL",
            equipment={"first_aid"},
        )
    ]

    assert select_ambulance(
        make_report(),
        ambulances,
        {"oxygen"},
    ) is None


def test_checks_patient_capacity():
    ambulances = [
        Ambulance(
            id="AMB-01",
            current_location_id="HOSTEL",
            equipment={"first_aid"},
            capacity=2,
        )
    ]

    assert select_ambulance(
        make_report(people_affected=3),
        ambulances,
        {"first_aid"},
    ) is None


def test_returns_none_when_no_ambulances_exist():
    assert select_ambulance(make_report(), []) is None
