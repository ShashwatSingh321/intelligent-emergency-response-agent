
from emergency_response.database.emergency_repository import (
    EmergencyRepository,
)
from emergency_response.models.emergency import (
    EmergencyReport,
    EmergencyStatus,
)


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
    """Validate and persist emergency status transitions."""

    def __init__(self, repository: EmergencyRepository):
        self.repository = repository

    def transition(
        self,
        report_id: str,
        new_status: EmergencyStatus,
    ) -> EmergencyReport:
        """Change a report's status if the transition is permitted."""

        report = self.repository.get_by_id(report_id)

        if report is None:
            raise KeyError(f"Report not found: {report_id}")

        allowed = ALLOWED_TRANSITIONS[report.status]

        if new_status not in allowed:
            raise ValueError(
                f"Cannot transition emergency from "
                f"'{report.status.value}' to '{new_status.value}'."
            )

        updated_report = report.model_copy(
            update={"status": new_status}
        )

        return self.repository.update(updated_report)
