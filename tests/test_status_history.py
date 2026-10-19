
from datetime import datetime, timezone

import pytest

from emergency_response.database.emergency_repository import (
    EmergencyRepository,
)
from emergency_response.database.status_history_repository import (
    StatusHistoryRepository,
)
from emergency_response.models.emergency import (
    EmergencyReport,
    EmergencyStatus,
)
from emergency_response.services.emergency_status_service import (
    EmergencyStatusService,
)


@pytest.fixture
def setup_status_service(tmp_path):
    emergency_repository = EmergencyRepository(
        tmp_path / "emergencies.json"
    )
    history_repository = StatusHistoryRepository(
        tmp_path / "status_history.json"
    )
    service = EmergencyStatusService(
        emergency_repository,
        history_repository,
    )

    report = EmergencyReport(
        id="ER-001",
        description="Patient needs urgent medical help",
        location_id="BUILDING-A",
        emergency_type="medical",
        priority=1,
        people_affected=1,
    )
    emergency_repository.save(report)

    return service, emergency_repository, history_repository, report


def test_records_successful_status_transition(setup_status_service):
    service, _, history_repository, report = setup_status_service

    service.transition(report.id, EmergencyStatus.UNDER_REVIEW)

    history = history_repository.list_for_report(report.id)

    assert len(history) == 1
    assert history[0].report_id == report.id
    assert history[0].previous_status == EmergencyStatus.REPORTED
    assert history[0].new_status == EmergencyStatus.UNDER_REVIEW


def test_records_utc_timestamp(setup_status_service):
    service, _, history_repository, report = setup_status_service

    before = datetime.now(timezone.utc)
    service.transition(report.id, EmergencyStatus.UNDER_REVIEW)
    after = datetime.now(timezone.utc)

    entry = history_repository.list_for_report(report.id)[0]

    assert before <= entry.changed_at <= after
    assert entry.changed_at.tzinfo is not None
    assert entry.changed_at.utcoffset().total_seconds() == 0


def test_rejected_transition_does_not_record_history(
    setup_status_service,
):
    service, _, history_repository, report = setup_status_service

    with pytest.raises(ValueError):
        service.transition(report.id, EmergencyStatus.RESOLVED)

    assert history_repository.list_for_report(report.id) == []


def test_unknown_report_does_not_record_history(setup_status_service):
    service, _, history_repository, _ = setup_status_service

    with pytest.raises(KeyError):
        service.transition("UNKNOWN-ID", EmergencyStatus.UNDER_REVIEW)

    assert history_repository.list_for_report("UNKNOWN-ID") == []


def test_records_multiple_transitions_in_order(setup_status_service):
    service, _, history_repository, report = setup_status_service

    service.transition(report.id, EmergencyStatus.UNDER_REVIEW)
    service.transition(report.id, EmergencyStatus.ASSIGNED)
    service.transition(report.id, EmergencyStatus.RESPONDING)

    history = history_repository.list_for_report(report.id)

    assert len(history) == 3
    assert [
        (entry.previous_status, entry.new_status)
        for entry in history
    ] == [
        (EmergencyStatus.REPORTED, EmergencyStatus.UNDER_REVIEW),
        (EmergencyStatus.UNDER_REVIEW, EmergencyStatus.ASSIGNED),
        (EmergencyStatus.ASSIGNED, EmergencyStatus.RESPONDING),
    ]
