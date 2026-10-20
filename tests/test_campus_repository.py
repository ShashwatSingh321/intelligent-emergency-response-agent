
import json

from emergency_response.database.campus_repository import (
    CampusKnowledgeRepository,
)


def test_imports_locations_and_connections(tmp_path):
    map_path = tmp_path / "campus_map.json"
    map_path.write_text(
        json.dumps(
            {
                "locations": [
                    {"id": "GATE", "name": "Main Gate"},
                    {"id": "LIBRARY", "name": "Library"},
                ],
                "connections": [
                    {
                        "source": "GATE",
                        "destination": "LIBRARY",
                        "weight": 2.0,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    repository = CampusKnowledgeRepository(tmp_path / "campus.db")
    repository.import_campus_map(map_path)

    assert repository.list_locations() == [
        {"id": "LIBRARY", "name": "Library"},
        {"id": "GATE", "name": "Main Gate"},
    ]

    graph = repository.load_graph()
    assert graph.has_location("GATE")
    assert graph.get_neighbors("GATE")["LIBRARY"] == 2.0


def test_resolves_english_and_hindi_aliases(tmp_path):
    map_path = tmp_path / "campus_map.json"
    map_path.write_text(
        json.dumps(
            {
                "locations": [
                    {"id": "MAIN_GATE", "name": "Main Gate"},
                    {"id": "LIBRARY", "name": "Central Library"},
                    {"id": "HOSTEL", "name": "Student Hostel"},
                    {"id": "AUDITORIUM", "name": "Auditorium"},
                    {"id": "MEDICAL_CENTER", "name": "Medical Center"},
                    {"id": "SPORTS_GROUND", "name": "Sports Ground"},
                ],
                "connections": [],
            }
        ),
        encoding="utf-8",
    )

    repository = CampusKnowledgeRepository(tmp_path / "campus.db")
    repository.import_campus_map(map_path)

    assert repository.resolve_location("the main gate") == "MAIN_GATE"
    assert repository.resolve_location("लाइब्रेरी") == "LIBRARY"
    assert repository.resolve_location("unknown building") is None
    assert repository.resolve_location(None) is None


def test_import_is_repeatable(tmp_path):
    map_path = tmp_path / "campus_map.json"
    map_path.write_text(
        json.dumps(
            {
                "locations": [
                    {"id": "MAIN_GATE", "name": "Main Gate"},
                ],
                "connections": [],
            }
        ),
        encoding="utf-8",
    )

    repository = CampusKnowledgeRepository(tmp_path / "campus.db")
    repository.import_campus_map(map_path)
    repository.import_campus_map(map_path)

    assert repository.list_locations() == [
        {"id": "MAIN_GATE", "name": "Main Gate"}
    ]
    assert repository.resolve_location("मुख्य द्वार") == "MAIN_GATE"
