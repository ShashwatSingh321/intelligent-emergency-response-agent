
import json
from pathlib import Path

from emergency_response.models.ambulance import Ambulance
from emergency_response.routing.graph import CampusGraph


def load_campus_graph(path: str | Path) -> CampusGraph:
    """Load campus locations and connections from a JSON file."""
    path = Path(path)

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    graph = CampusGraph()

    for location in data["locations"]:
        graph.add_location(location["id"])

    for connection in data["connections"]:
        graph.add_connection(
            source=connection["source"],
            destination=connection["destination"],
            weight=connection["weight"],
            bidirectional=connection.get("bidirectional", True),
        )

    return graph


def load_ambulances(path: str | Path) -> list[Ambulance]:
    """Load and validate ambulance records from a JSON file."""
    path = Path(path)

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return [
        Ambulance.model_validate(record)
        for record in data["ambulances"]
    ]
