
from math import inf

from emergency_response.models.ambulance import Ambulance, AmbulanceStatus
from emergency_response.models.emergency import EmergencyReport
from emergency_response.routing.dijkstra import dijkstra
from emergency_response.routing.graph import CampusGraph


def select_ambulance_by_route(
    report: EmergencyReport,
    ambulances: list[Ambulance],
    graph: CampusGraph,
    required_equipment: set[str] | None = None,
) -> tuple[Ambulance | None, list[str], float]:
    """
    Select an eligible ambulance with the lowest route cost.

    Returns:
        (selected_ambulance, route, route_cost)

    If no suitable ambulance can reach the emergency, returns:
        (None, [], infinity)
    """
    required_equipment = required_equipment or set()

    best_ambulance = None
    best_route = []
    best_cost = inf

    for ambulance in ambulances:
        if ambulance.status != AmbulanceStatus.AVAILABLE:
            continue

        if ambulance.capacity < report.people_affected:
            continue

        if not required_equipment.issubset(ambulance.equipment):
            continue

        if not graph.has_location(ambulance.current_location_id):
            continue

        if not graph.has_location(report.location_id):
            continue

        route, cost = dijkstra(
            graph,
            ambulance.current_location_id,
            report.location_id,
        )

        if not route:
            continue

        if (
            cost < best_cost
            or (
                cost == best_cost
                and (
                    best_ambulance is None
                    or ambulance.id < best_ambulance.id
                )
            )
        ):
            best_ambulance = ambulance
            best_route = route
            best_cost = cost

    if best_ambulance is None:
        return None, [], inf

    return best_ambulance, best_route, best_cost
