
from emergency_response.database.emergency_repository import (
    EmergencyRepository,
)
from emergency_response.models.ambulance import Ambulance
from emergency_response.models.emergency import (
    EmergencyReport,
    EmergencyStatus,
)
from emergency_response.routing.graph import CampusGraph
from emergency_response.services.emergency_service import (
    EmergencyProcessingResult,
    process_emergency,
)
from emergency_response.services.emergency_status_service import (
    EmergencyStatusService,
)


class EmergencyWorkflow:
    """Coordinate report validation, persistence, and processing."""

    def __init__(
        self,
        repository: EmergencyRepository,
        graph: CampusGraph,
        ambulances: list[Ambulance],
    ):
        self.repository = repository
        self.graph = graph
        self.ambulances = ambulances
        self.status_service = EmergencyStatusService(repository)

    def submit_report(
        self,
        report: EmergencyReport,
        required_equipment: set[str] | None = None,
    ) -> EmergencyProcessingResult:
        """Validate, save, and process an emergency report."""

        if not self.graph.has_location(report.location_id):
            raise ValueError(
                f"Unknown campus location: {report.location_id}"
            )

        self.repository.save(report)

        return process_emergency(
            report=report,
            ambulances=self.ambulances,
            graph=self.graph,
            required_equipment=required_equipment,
        )

    def transition_status(
        self,
        report_id: str,
        new_status: EmergencyStatus,
    ) -> EmergencyReport:
        """Change a report's status using validated transitions."""

        return self.status_service.transition(report_id, new_status)

    def get_report(self, report_id: str) -> EmergencyReport | None:
        """Retrieve a previously saved report."""

        return self.repository.get_by_id(report_id)

    def list_reports(self) -> list[EmergencyReport]:
        """List all saved reports."""

        return self.repository.list_all()
