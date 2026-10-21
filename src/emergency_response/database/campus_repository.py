import json
import sqlite3
from pathlib import Path

from emergency_response.routing.graph import CampusGraph


DEFAULT_ALIASES = {
    "MAIN_GATE": [
        "main gate", "main entrance", "gate",
        "मुख्य द्वार", "मुख्य गेट",
    ],
    "LIBRARY": [
        "central library", "library",
        "पुस्तकालय", "लाइब्रेरी",
    ],
    "HOSTEL": [
        "student hostel", "hostel",
        "छात्रावास", "हॉस्टल",
    ],
    "AUDITORIUM": [
        "auditorium", "ऑडिटोरियम",
    ],
    "MEDICAL_CENTER": [
        "medical center", "medical centre",
        "health center", "health centre",
        "चिकित्सा केंद्र", "मेडिकल सेंटर",
    ],
    "SPORTS_GROUND": [
        "sports ground", "sports field",
        "खेल का मैदान", "स्पोर्ट्स ग्राउंड",
    ],
}


class CampusKnowledgeRepository:
    """SQLite storage for campus locations, aliases, and connections."""

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(
            parents=True, exist_ok=True
        )
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS locations (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS location_aliases (
                    alias TEXT NOT NULL,
                    normalized_alias TEXT NOT NULL UNIQUE,
                    location_id TEXT NOT NULL,
                    FOREIGN KEY(location_id)
                        REFERENCES locations(id)
                        ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS connections (
                    source TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    weight REAL NOT NULL CHECK(weight > 0),
                    bidirectional INTEGER NOT NULL DEFAULT 1,
                    PRIMARY KEY(source, destination),
                    FOREIGN KEY(source) REFERENCES locations(id),
                    FOREIGN KEY(destination) REFERENCES locations(id)
                );

                CREATE TABLE IF NOT EXISTS facilities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    details TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY(location_id)
                        REFERENCES locations(id)
                        ON DELETE CASCADE
                );
                """
            )

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join(value.casefold().split())

    def import_campus_map(self, json_path: str | Path) -> None:
        """Import the existing JSON map and known aliases into SQLite."""

        source_path = Path(json_path)
        with source_path.open("r", encoding="utf-8") as file:
            campus_map = json.load(file)

        locations = campus_map.get("locations", [])
        connections = campus_map.get("connections", [])

        if not locations:
            raise ValueError("Campus map must contain locations.")

        location_ids = {
            item["id"] for item in locations
            if item.get("id") and item.get("name")
        }
        if len(location_ids) != len(locations):
            raise ValueError("Every location needs a unique ID and name.")

        for edge in connections:
            if (
                edge.get("source") not in location_ids
                or edge.get("destination") not in location_ids
                or edge.get("weight", 0) <= 0
            ):
                raise ValueError(
                    "Campus connections must reference valid locations "
                    "and have positive weights."
                )

        with self._connect() as connection:
            for item in locations:
                connection.execute(
                    """
                    INSERT INTO locations(id, name)
                    VALUES (?, ?)
                    ON CONFLICT(id) DO UPDATE SET name = excluded.name
                    """,
                    (item["id"], item["name"]),
                )

            for location_id, aliases in DEFAULT_ALIASES.items():
                if location_id not in location_ids:
                    continue

                for alias in aliases:
                    normalized = self._normalize(alias)
                    existing = connection.execute(
                        """
                        SELECT location_id FROM location_aliases
                        WHERE normalized_alias = ?
                        """,
                        (normalized,),
                    ).fetchone()

                    if existing and existing["location_id"] != location_id:
                        raise ValueError(
                            f"Alias '{alias}' belongs to multiple locations."
                        )

                    connection.execute(
                        """
                        INSERT INTO location_aliases(
                            alias, normalized_alias, location_id
                        )
                        VALUES (?, ?, ?)
                        ON CONFLICT(normalized_alias) DO UPDATE SET
                            alias = excluded.alias,
                            location_id = excluded.location_id
                        """,
                        (alias, normalized, location_id),
                    )

            # Replace the imported road network so deleted JSON edges
            # do not remain in the database.
            connection.execute("DELETE FROM connections")

            for edge in connections:
                connection.execute(
                    """
                    INSERT INTO connections(
                        source, destination, weight, bidirectional
                    ) VALUES (?, ?, ?, 1)
                    """,
                    (
                        edge["source"],
                        edge["destination"],
                        float(edge["weight"]),
                    ),
                )

    def resolve_location(self, hint: str | None) -> str | None:
        """Resolve an exact alias or a unique alias within a longer phrase."""

        if not hint or not hint.strip():
            return None

        normalized_hint = self._normalize(hint)

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT normalized_alias, location_id
                FROM location_aliases
                ORDER BY LENGTH(normalized_alias) DESC
                """
            ).fetchall()

        matches = {
            row["location_id"]
            for row in rows
            if (
                normalized_hint == row["normalized_alias"]
                or f" {row['normalized_alias']} " in f" {normalized_hint} "
            )
        }

        return next(iter(matches)) if len(matches) == 1 else None

    def load_graph(self) -> CampusGraph:
        """Build the existing routing graph from stored campus data."""

        graph = CampusGraph()

        with self._connect() as connection:
            locations = connection.execute(
                "SELECT id FROM locations ORDER BY id"
            ).fetchall()
            edges = connection.execute(
                """
                SELECT source, destination, weight, bidirectional
                FROM connections
                ORDER BY source, destination
                """
            ).fetchall()

        for location in locations:
            graph.add_location(location["id"])

        for edge in edges:
            graph.add_connection(
                source=edge["source"],
                destination=edge["destination"],
                weight=edge["weight"],
                bidirectional=bool(edge["bidirectional"]),
            )

        return graph

    def list_locations(self) -> list[dict[str, str]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, name FROM locations ORDER BY name"
            ).fetchall()

        return [dict(row) for row in rows]

    def add_facility(
        self,
        location_id: str,
        name: str,
        details: str = "",
    ) -> dict:
        """Add a facility to an existing campus location."""

        location_id = location_id.strip().upper()
        name = name.strip()
        details = details.strip()

        if not location_id:
            raise ValueError("Location ID is required.")

        if not name:
            raise ValueError("Facility name is required.")

        with self._connect() as connection:
            location = connection.execute(
                "SELECT id FROM locations WHERE id = ?",
                (location_id,),
            ).fetchone()

            if location is None:
                raise ValueError(
                    f"Unknown campus location: {location_id}"
                )

            cursor = connection.execute(
                """
                INSERT INTO facilities(location_id, name, details)
                VALUES (?, ?, ?)
                """,
                (location_id, name, details),
            )

            facility_id = cursor.lastrowid

            row = connection.execute(
                """
                SELECT id, location_id, name, details
                FROM facilities
                WHERE id = ?
                """,
                (facility_id,),
            ).fetchone()

        return dict(row)

    def list_facilities(
        self,
        location_id: str | None = None,
    ) -> list[dict]:
        """List facilities, optionally filtered by campus location."""

        with self._connect() as connection:
            if location_id:
                rows = connection.execute(
                    """
                    SELECT
                        f.id,
                        f.location_id,
                        l.name AS location_name,
                        f.name,
                        f.details
                    FROM facilities AS f
                    JOIN locations AS l ON l.id = f.location_id
                    WHERE f.location_id = ?
                    ORDER BY f.name
                    """,
                    (location_id.strip().upper(),),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT
                        f.id,
                        f.location_id,
                        l.name AS location_name,
                        f.name,
                        f.details
                    FROM facilities AS f
                    JOIN locations AS l ON l.id = f.location_id
                    ORDER BY l.name, f.name
                    """
                ).fetchall()

        return [dict(row) for row in rows]

    def search_facilities(self, query: str) -> list[dict]:
        """Search facility names and details using a case-insensitive match."""

        query = query.strip()

        if not query:
            return []

        pattern = f"%{query}%"

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    f.id,
                    f.location_id,
                    l.name AS location_name,
                    f.name,
                    f.details
                FROM facilities AS f
                JOIN locations AS l ON l.id = f.location_id
                WHERE f.name LIKE ? COLLATE NOCASE
                   OR f.details LIKE ? COLLATE NOCASE
                ORDER BY l.name, f.name
                """,
                (pattern, pattern),
            ).fetchall()

        return [dict(row) for row in rows]