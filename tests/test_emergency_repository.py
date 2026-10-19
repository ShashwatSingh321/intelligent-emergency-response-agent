
import pytest

from emergency_response.database.emergency_repository import (
    EmergencyRepository,
)
from emergency_response.models.emergency import (
    EmergencyReport,
    EmergencyStatus,
    EmergencyType,
)


def make_report(report_id="ER-001"):
    return EmergencyReport(
        id=report_id,
        description="A student needs medical assistance",
        emergency_type=EmergencyType.MEDICAL,
        location_id="LIBRARY",
    )


def test_save_and_retrieve_report(tmp_path):
    repository = EmergencyRepository(tmp_path / "reports.json")
    report = make_report()

    repository.save(report)
    retrieved = repository.get_by_id("ER-001")

    assert retrieved == report


def test_list_all_reports(tmp_path):
    repository = EmergencyRepository(tmp_path / "reports.json")
    first = make_report("ER-001")
    second = make_report("ER-002")

    repository.save(first)
    repository.save(second)

    assert repository.list_all() == [first, second]


def test_duplicate_report_id_is_rejected(tmp_path):
    repository = EmergencyRepository(tmp_path / "reports.json")
    repository.save(make_report())

    with pytest.raises(ValueError, match="already exists"):
        repository.save(make_report())


def test_update_existing_report(tmp_path):
    repository = EmergencyRepository(tmp_path / "reports.json")
    report = make_report()
    repository.save(report)

    updated = report.model_copy(
        update={"status": EmergencyStatus.RESOLVED}
    )
    repository.update(updated)

    assert repository.get_by_id("ER-001").status == EmergencyStatus.RESOLVED
    assert len(repository.list_all()) == 1


def test_update_missing_report_raises_error(tmp_path):
    repository = EmergencyRepository(tmp_path / "reports.json")

    with pytest.raises(KeyError, match="Report not found"):
        repository.update(make_report())


def test_missing_report_returns_none(tmp_path):
    repository = EmergencyRepository(tmp_path / "reports.json")

    assert repository.get_by_id("UNKNOWN") is None
