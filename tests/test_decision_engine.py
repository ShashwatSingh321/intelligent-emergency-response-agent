
from emergency_response.agents.decision_engine import (
    calculate_priority,
    explain_priority,
)
from emergency_response.models.emergency import EmergencyReport, EmergencyType


def test_life_threatening_keyword_gets_highest_preliminary_priority():
    report = EmergencyReport(
        id="ER-101",
        description="A person is unconscious",
        location_id="LIBRARY",
    )

    assert calculate_priority(report) == 5


def test_multiple_people_get_high_priority():
    report = EmergencyReport(
        id="ER-102",
        description="Several people need assistance",
        location_id="GROUND",
        people_affected=5,
    )

    assert calculate_priority(report) == 4


def test_medical_report_has_at_least_standard_priority():
    report = EmergencyReport(
        id="ER-103",
        description="A student feels unwell",
        location_id="HOSTEL",
        emergency_type=EmergencyType.MEDICAL,
        priority=2,
    )

    assert calculate_priority(report) == 3


def test_priority_explanation_is_returned():
    report = EmergencyReport(
        id="ER-104",
        description="A person is unconscious",
        location_id="LIBRARY",
    )

    assert "human review" in explain_priority(report)
