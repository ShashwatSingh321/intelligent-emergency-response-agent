
import pytest

from emergency_response.database.emergency_repository import (
    EmergencyRepository,
)
from emergency_response.models.emergency import (
    EmergencyReport,
    EmergencyStatus,
)
from emergency_response.services.emergency_status_service import (
    EmergencyStatusService,
)


def make_report(report_id="ER-STATUS-001"):
    return EmergencyReport(
        id=report_id,
        description="A student needs medical assistance",
        location_id="LIBRARY",
    )


def make_service(tmp_path):
    repository = EmergencyRepository(tmp_path / "reports.json")
    return repository, EmergencyStatusService(repository)


def test_report_can_move_to_under_review(tmp_path):
    repository, service = make_service(tmp_path)
    report = make_report()
    repository.save(report)

    updated = service.transition(
        report.id,
        EmergencyStatus.UNDER_REVIEW,
    )

    assert updated.status == EmergencyStatus.UNDER_REVIEW
    assert repository.get_by_id(report.id).status == (
        EmergencyStatus.UNDER_REVIEW
    )


def test_report_can_be_assigned_after_review(tmp_path):
    repository, service = make_service(tmp_path)
    report = make_report()
    report.status = EmergencyStatus.UNDER_REVIEW
    repository.save(report)

    updated = service.transition(
        report.id,
        EmergencyStatus.ASSIGNED,
    )

    assert updated.status == EmergencyStatus.ASSIGNED


def test_invalid_transition_is_rejected(tmp_path):
    repository, service = make_service(tmp_path)
    report = make_report()
    repository.save(report)

    with pytest.raises(ValueError, match="Cannot transition"):
        service.transition(
            report.id,
            EmergencyStatus.RESOLVED,
        )

    assert repository.get_by_id(report.id).status == (
        EmergencyStatus.REPORTED
    )


def test_resolved_report_cannot_change_status(tmp_path):
    repository, service = make_service(tmp_path)
    report = make_report()
    report.status = EmergencyStatus.RESOLVED
    repository.save(report)

    with pytest.raises(ValueError, match="Cannot transition"):
        service.transition(
            report.id,
            EmergencyStatus.CANCELLED,
        )


def test_missing_report_raises_error(tmp_path):
    _, service = make_service(tmp_path)

    with pytest.raises(KeyError, match="Report not found"):
        service.transition(
            "UNKNOWN-REPORT",
            EmergencyStatus.UNDER_REVIEW,
        )


def test_cancellation_is_allowed_before_resolution(tmp_path):
    repository, service = make_service(tmp_path)
    report = make_report()
    repository.save(report)

    updated = service.transition(
        report.id,
        EmergencyStatus.CANCELLED,
    )

    assert updated.status == EmergencyStatus.CANCELLED
