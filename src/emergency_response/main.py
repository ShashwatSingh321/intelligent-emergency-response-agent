
from pathlib import Path

from emergency_response.database.repository import (
    load_ambulances,
    load_campus_graph,
)
from emergency_response.models.emergency import (
    EmergencyReport,
    EmergencyType,
)
from emergency_response.services.dispatch_service import (
    select_ambulance_by_route,
)


def main() -> None:
    # Locate the project root and load our sample data.
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"

    graph = load_campus_graph(data_dir / "campus_map.json")
    ambulances = load_ambulances(data_dir / "sample_ambulances.json")

    # Create a sample emergency report.
    report = EmergencyReport(
        id="ER-DEMO-001",
        description="A student has suffered an injury",
        emergency_type=EmergencyType.MEDICAL,
        location_id="LIBRARY",
        people_affected=1,
    )

    # Select an ambulance with the required equipment.
    ambulance, route, cost = select_ambulance_by_route(
        report=report,
        ambulances=ambulances,
        graph=graph,
        required_equipment={"first_aid"},
    )

    print("\n=== Intelligent Emergency Response Agent ===")
    print(f"Report ID: {report.id}")
    print(f"Emergency type: {report.emergency_type.value}")
    print(f"Description: {report.description}")
    print(f"Reported location: {report.location_id}")
    print(f"People affected: {report.people_affected}")

    if ambulance is None:
        print("\nNo suitable reachable ambulance is available.")
        print("A human dispatcher must review the situation.")
        return

    print("\n--- Dispatch Recommendation ---")
    print(f"Selected ambulance: {ambulance.id}")
    print(f"Starting location: {ambulance.current_location_id}")
    print(f"Route: {' -> '.join(route)}")
    print(f"Total route cost: {cost:g} cost units")
    print("Required equipment: first_aid")
    print("\nThis is a prototype recommendation, not a real dispatch.")


if __name__ == "__main__":
    main()
