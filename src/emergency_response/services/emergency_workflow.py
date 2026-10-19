
from emergency_response.database.emergency_repository import (
    EmergencyRepository,
)
from emergency_response.models.ambulance import Ambulance
from emergency_response.models.emergency import EmergencyReport
from emergency_response.routing.graph import CampusGraph
from emergency_response.services.emergency_service import (
    EmergencyProcessingResult,
    process_emergency,
)


class EmergencyWorkflow:
    """Coordinate report persistence and preliminary processing."""

    def __init__(
        self,
        repository: EmergencyRepository,
        graph: CampusGraph,
        ambulances: list[Ambulance],
    ):
        self.repository = repository
        self.graph = graph
        self.ambulances = ambulances

    def submit_report(
        self,
        report: EmergencyReport,
        required_equipment: set[str] | None = None,
    ) -> EmergencyProcessingResult:
        """Save a new report, then produce a processing recommendation."""

        # Save first so duplicate IDs are rejected before processing.
        self.repository.save(report)

        return process_emergency(
            report=report,
            ambulances=self.ambulances,
            graph=self.graph,
            required_equipment=required_equipment,
        )

    def get_report(self, report_id: str) -> EmergencyReport | None:
        """Retrieve a previously saved report."""
        return self.repository.get_by_id(report_id)

    def list_reports(self) -> list[EmergencyReport]:
        """List all saved reports."""
        return self.repository.list_all()
