
from pathlib import Path

from emergency_response.database.emergency_repository import (
    EmergencyRepository,
)
from emergency_response.database.repository import (
    load_ambulances,
    load_campus_graph,
)
from emergency_response.models.emergency import (
    EmergencyReport,
    EmergencyType,
)
from emergency_response.services.emergency_workflow import (
    EmergencyWorkflow,
)


def main() -> None:
    # Locate the project root and load sample data.
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"

    graph = load_campus_graph(data_dir / "campus_map.json")
    ambulances = load_ambulances(data_dir / "sample_ambulances.json")

    # Store reports in the project's data directory.
    repository = EmergencyRepository(data_dir / "emergency_reports.json")

    workflow = EmergencyWorkflow(
        repository=repository,
        graph=graph,
        ambulances=ambulances,
    )

    # Create a sample emergency report.
    report = EmergencyReport(
        id="ER-DEMO-001",
        description="A student has suffered an injury",
        emergency_type=EmergencyType.MEDICAL,
        location_id="LIBRARY",
        people_affected=1,
    )

    try:
        result = workflow.submit_report(
            report=report,
            required_equipment={"first_aid"},
        )
    except ValueError as error:
        print(f"\nCould not submit report: {error}")
        print(
            "The demo report ID may already exist. "
            "Use a new ID to submit another report."
        )
        return

    print("\n=== Intelligent Emergency Response Agent ===")
    print(f"Report ID: {result.report_id}")
    print(f"Emergency type: {report.emergency_type.value}")
    print(f"Description: {report.description}")
    print(f"Reported location: {report.location_id}")
    print(f"People affected: {report.people_affected}")
    print(f"Preliminary priority: {result.priority}")
    print(f"Priority explanation: {result.priority_explanation}")

    if result.ambulance is None:
        print("\nNo suitable reachable ambulance is available.")
        print("A human dispatcher must review the situation.")
    else:
        print("\n--- Dispatch Recommendation ---")
        print(f"Selected ambulance: {result.ambulance.id}")
        print(
            "Starting location: "
            f"{result.ambulance.current_location_id}"
        )
        print(f"Route: {' -> '.join(result.route)}")
        print(f"Total route cost: {result.route_cost:g} cost units")
        print("Required equipment: first_aid")

    print(f"\nRecommendation: {result.recommendation}")
    print("Report saved to data/emergency_reports.json")
    print("\nThis is a prototype recommendation, not a real dispatch.")


if __name__ == "__main__":
    main()
