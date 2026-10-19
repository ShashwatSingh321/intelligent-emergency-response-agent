
import pytest
from pydantic import ValidationError

from emergency_response.models.emergency import (
    EmergencyReport,
    EmergencyStatus,
    EmergencyType,
)


def test_emergency_report_defaults():
    report = EmergencyReport(
        id="ER-001",
        description="A student has injured their leg",
        location_id="LIBRARY",
    )

    assert report.emergency_type == EmergencyType.OTHER
    assert report.status == EmergencyStatus.REPORTED
    assert report.priority == 3
    assert report.people_affected == 1


def test_emergency_priority_must_be_between_one_and_five():
    with pytest.raises(ValidationError):
        EmergencyReport(
            id="ER-002",
            description="Medical emergency",
            location_id="HOSTEL",
            priority=6,
        )


def test_emergency_description_cannot_be_too_short():
    with pytest.raises(ValidationError):
        EmergencyReport(
            id="ER-003",
            description="Hi",
            location_id="HOSTEL",
        )
