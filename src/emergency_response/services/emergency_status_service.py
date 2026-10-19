
from pathlib import Path

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
from emergency_response.models.status_history import StatusHistoryEntry


ALLOWED_TRANSITIONS: dict[
    EmergencyStatus, set[EmergencyStatus]
] = {
    EmergencyStatus.REPORTED: {
        EmergencyStatus.UNDER_REVIEW,
        EmergencyStatus.CANCELLED,
    },
    EmergencyStatus.UNDER_REVIEW: {
        EmergencyStatus.ASSIGNED,
        EmergencyStatus.CANCELLED,
    },
    EmergencyStatus.ASSIGNED: {
        EmergencyStatus.RESPONDING,
        EmergencyStatus.CANCELLED,
    },
    EmergencyStatus.RESPONDING: {
        EmergencyStatus.RESOLVED,
        EmergencyStatus.CANCELLED,
    },
    EmergencyStatus.RESOLVED: set(),
    EmergencyStatus.CANCELLED: set(),
}


class EmergencyStatusService:
    """Validate status transitions and record their history."""

    def __init__(
        self,
        repository: EmergencyRepository,
        history_repository: StatusHistoryRepository | None = None,
    ):
        self.repository = repository

        if history_repository is None:
            history_path = (
                Path(repository.path).parent / "status_history.json"
            )
            history_repository = StatusHistoryRepository(history_path)

        self.history_repository = history_repository

    def transition(
        self,
        report_id: str,
        new_status: EmergencyStatus,
    ) -> EmergencyReport:
        """Change status and record the successful transition."""

        report = self.repository.get_by_id(report_id)

        if report is None:
            raise KeyError(f"Report not found: {report_id}")

        allowed = ALLOWED_TRANSITIONS[report.status]

        if new_status not in allowed:
            raise ValueError(
                f"Cannot transition emergency from "
                f"'{report.status.value}' to '{new_status.value}'."
            )

        previous_status = report.status

        updated_report = report.model_copy(
            update={"status": new_status}
        )

        saved_report = self.repository.update(updated_report)

        self.history_repository.record(
            StatusHistoryEntry(
                report_id=report_id,
                previous_status=previous_status,
                new_status=new_status,
            )
        )

        return saved_report

    def get_history(
        self,
        report_id: str,
    ) -> list[StatusHistoryEntry]:
        """Return recorded status changes for an emergency."""
        return self.history_repository.list_for_report(report_id)
