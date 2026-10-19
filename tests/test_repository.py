
from pathlib import Path

from emergency_response.database.repository import (
    load_ambulances,
    load_campus_graph,
)


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def test_load_campus_graph():
    graph = load_campus_graph(DATA / "campus_map.json")

    assert graph.has_location("MAIN_GATE")
    assert graph.has_location("MEDICAL_CENTER")
    assert "LIBRARY" in graph.get_neighbors("MAIN_GATE")


def test_load_ambulances():
    ambulances = load_ambulances(DATA / "sample_ambulances.json")

    assert len(ambulances) == 3
    assert ambulances[0].id == "AMB-01"


def test_loaded_ambulance_status_is_validated():
    ambulances = load_ambulances(DATA / "sample_ambulances.json")

    available = [a for a in ambulances if a.status.value == "available"]
    assert len(available) == 2
