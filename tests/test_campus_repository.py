import json

import pytest

from emergency_response.database.campus_repository import (
    CampusKnowledgeRepository,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

CAMPUS_MAP_PATH = "data/campus_map.json"  # adjust to your project's map path


@pytest.fixture
def repository(tmp_path):
    """Fresh repository backed by a throwaway SQLite database."""
    return CampusKnowledgeRepository(tmp_path / "campus.db")


# ---------------------------------------------------------------------------
# Existing tests
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# New facility tests
# ---------------------------------------------------------------------------

def test_add_and_list_facilities(repository):
    repository.import_campus_map(CAMPUS_MAP_PATH)

    facility = repository.add_facility(
        "LIBRARY",
        "First Aid Kit",
        "Sample test record; verify before real use.",
    )

    assert facility["location_id"] == "LIBRARY"
    assert facility["name"] == "First Aid Kit"

    facilities = repository.list_facilities("LIBRARY")

    assert len(facilities) == 1
    assert facilities[0]["location_name"] == "Central Library"
    assert facilities[0]["details"] == (
        "Sample test record; verify before real use."
    )


def test_add_facility_rejects_unknown_location(repository):
    repository.import_campus_map(CAMPUS_MAP_PATH)

    with pytest.raises(ValueError, match="Unknown campus location"):
        repository.add_facility("UNKNOWN", "First Aid Kit")


def test_add_facility_rejects_blank_name(repository):
    repository.import_campus_map(CAMPUS_MAP_PATH)

    with pytest.raises(ValueError, match="Facility name is required"):
        repository.add_facility("LIBRARY", "   ")


def test_search_facilities(repository):
    repository.import_campus_map(CAMPUS_MAP_PATH)

    repository.add_facility(
        "LIBRARY",
        "First Aid Kit",
        "Sample test record",
    )
    repository.add_facility(
        "HOSTEL",
        "Security Desk",
        "Sample test record",
    )

    results = repository.search_facilities("first aid")

    assert len(results) == 1
    assert results[0]["name"] == "First Aid Kit"


def test_hindi_aliases_resolve(repository):
    repository.import_campus_map(CAMPUS_MAP_PATH)

    assert repository.resolve_location("मुख्य द्वार") == "MAIN_GATE"
    assert repository.resolve_location("पुस्तकालय") == "LIBRARY"
    assert repository.resolve_location("छात्रावास") == "HOSTEL"