
import pytest

from emergency_response.agents.decision_engine import (
    calculate_priority,
    explain_priority,
)
from emergency_response.models.emergency import (
    EmergencyReport,
    EmergencyType,
)


@pytest.mark.parametrize(
    "description",
    [
        "A person is unconscious",
        "The patient is not breathing",
        "There is severe bleeding",
        "Possible cardiac arrest",
        "There is a fire in the building",
        "A person is trapped",
    ],
)
def test_life_threatening_keyword_gets_highest_preliminary_priority(
    description,
):
    report = EmergencyReport(
        id="ER-101",
        description=description,
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


def test_more_than_five_people_get_high_priority():
    report = EmergencyReport(
        id="ER-105",
        description="A crowd needs assistance",
        location_id="GROUND",
        people_affected=8,
        priority=2,
    )

    assert calculate_priority(report) == 4


def test_critical_keyword_takes_precedence_over_people_count():
    report = EmergencyReport(
        id="ER-106",
        description="A person is unconscious",
        location_id="LIBRARY",
        people_affected=1,
        priority=2,
    )

    assert calculate_priority(report) == 5


def test_medical_report_has_at_least_standard_priority():
    report = EmergencyReport(
        id="ER-103",
        description="A student feels unwell",
        location_id="HOSTEL",
        emergency_type=EmergencyType.MEDICAL,
        priority=2,
    )

    assert calculate_priority(report) == 3


@pytest.mark.parametrize(
    "emergency_type",
    [
        EmergencyType.MEDICAL,
        EmergencyType.FIRE,
        EmergencyType.ACCIDENT,
        EmergencyType.SECURITY,
    ],
)
def test_supported_emergency_categories_have_at_least_priority_three(
    emergency_type,
):
    report = EmergencyReport(
        id="ER-107",
        description="Assistance is required",
        location_id="LIBRARY",
        emergency_type=emergency_type,
        priority=1,
    )

    assert calculate_priority(report) == 3


def test_existing_higher_priority_is_preserved():
    report = EmergencyReport(
        id="ER-108",
        description="A student feels unwell",
        location_id="HOSTEL",
        emergency_type=EmergencyType.MEDICAL,
        priority=4,
    )

    assert calculate_priority(report) == 4


def test_priority_explanation_mentions_matched_critical_keyword():
    report = EmergencyReport(
        id="ER-104",
        description="A person is unconscious",
        location_id="LIBRARY",
    )

    explanation = explain_priority(report)

    assert "unconscious" in explanation
    assert "human review" in explanation


def test_priority_explanation_mentions_affected_people():
    report = EmergencyReport(
        id="ER-109",
        description="Several people need assistance",
        location_id="GROUND",
        people_affected=5,
    )

    explanation = explain_priority(report)

    assert "5 people" in explanation
    assert "human review" in explanation


def test_lower_priority_explanation_does_not_claim_situation_is_safe():
    report = EmergencyReport(
        id="ER-110",
        description="A minor issue was reported",
        location_id="HOSTEL",
        emergency_type=EmergencyType.OTHER,
        priority=1,
    )

    explanation = explain_priority(report)

    assert "Lower preliminary priority" in explanation
    assert "does not establish that the situation is safe" in explanation
