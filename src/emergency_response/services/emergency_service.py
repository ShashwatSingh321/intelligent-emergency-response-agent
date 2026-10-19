
from dataclasses import dataclass
from math import inf

from emergency_response.agents.decision_engine import (
    calculate_priority,
    explain_priority,
)
from emergency_response.models.ambulance import Ambulance
from emergency_response.models.emergency import EmergencyReport
from emergency_response.routing.graph import CampusGraph
from emergency_response.services.dispatch_service import (
    select_ambulance_by_route,
)


@dataclass
class EmergencyProcessingResult:
    """Structured result of preliminary emergency processing."""

    report_id: str
    priority: int
    priority_explanation: str
    ambulance: Ambulance | None
    route: list[str]
    route_cost: float
    recommendation: str

    @property
    def ambulance_found(self) -> bool:
        return self.ambulance is not None

    @property
    def route_found(self) -> bool:
        return bool(self.route) and self.route_cost != inf


def process_emergency(
    report: EmergencyReport,
    ambulances: list[Ambulance],
    graph: CampusGraph,
    required_equipment: set[str] | None = None,
) -> EmergencyProcessingResult:
    """
    Assess an emergency and recommend a suitable ambulance and route.

    This function produces a recommendation only. It does not dispatch
    a real vehicle or change the report's status.
    """

    priority = calculate_priority(report)
    priority_explanation = explain_priority(report)

    ambulance, route, route_cost = select_ambulance_by_route(
        report=report,
        ambulances=ambulances,
        graph=graph,
        required_equipment=required_equipment,
    )

    if ambulance is None:
        recommendation = (
            "No suitable reachable ambulance was found. "
            "Escalate for human review and alternative arrangements."
        )
    else:
        recommendation = (
            f"Ambulance {ambulance.id} is recommended for human review. "
            f"Estimated route cost: {route_cost}."
        )

    return EmergencyProcessingResult(
        report_id=report.id,
        priority=priority,
        priority_explanation=priority_explanation,
        ambulance=ambulance,
        route=route,
        route_cost=route_cost,
        recommendation=recommendation,
    )
