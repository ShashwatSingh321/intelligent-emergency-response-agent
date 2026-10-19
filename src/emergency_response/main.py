
from pathlib import Path
from uuid import uuid4

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


def get_emergency_input() -> EmergencyReport:
    """Collect an emergency report from terminal input."""
    print("\n=== Submit an Emergency Report ===")

    while True:
        description = input("Describe the emergency: ").strip()
        if len(description) >= 3:
            break
        print("Please enter at least 3 characters.")

    emergency_types = list(EmergencyType)
    print("\nEmergency types:")
    for index, emergency_type in enumerate(emergency_types, start=1):
        print(f"{index}. {emergency_type.value.title()}")

    while True:
        try:
            choice = int(input("Select emergency type (number): "))
            if 1 <= choice <= len(emergency_types):
                emergency_type = emergency_types[choice - 1]
                break
        except ValueError:
            pass
        print("Invalid choice. Enter a number from the list.")

    locations = [
        ("MAIN_GATE", "Main Gate"),
        ("LIBRARY", "Central Library"),
        ("HOSTEL", "Student Hostel"),
        ("AUDITORIUM", "Auditorium"),
        ("MEDICAL_CENTER", "Medical Center"),
        ("SPORTS_GROUND", "Sports Ground"),
    ]

    print("\nCampus locations:")
    for index, (location_id, location_name) in enumerate(
        locations, start=1
    ):
        print(f"{index}. {location_name} ({location_id})")

    while True:
        try:
            choice = int(input("Select reported location (number): "))
            if 1 <= choice <= len(locations):
                location_id = locations[choice - 1][0]
                break
        except ValueError:
            pass
        print("Invalid choice. Enter a number from the list.")

    while True:
        try:
            people_affected = int(
                input("Number of people affected: ")
            )
            if people_affected >= 1:
                break
        except ValueError:
            pass
        print("Enter a whole number greater than or equal to 1.")

    return EmergencyReport(
        id=f"ER-{uuid4().hex[:12].upper()}",
        description=description,
        emergency_type=emergency_type,
        location_id=location_id,
        people_affected=people_affected,
    )


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"

    graph = load_campus_graph(data_dir / "campus_map.json")
    ambulances = load_ambulances(data_dir / "sample_ambulances.json")

    repository = EmergencyRepository(
        data_dir / "emergency_reports.json"
    )
    workflow = EmergencyWorkflow(
        repository=repository,
        graph=graph,
        ambulances=ambulances,
    )

    try:
        report = get_emergency_input()
        result = workflow.submit_report(
            report=report,
            required_equipment={"first_aid"},
        )
    except KeyboardInterrupt:
        print("\nEmergency report input cancelled.")
        return
    except (ValueError, EOFError) as error:
        print(f"\nCould not submit emergency report: {error}")
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
