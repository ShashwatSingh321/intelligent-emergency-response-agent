
from dataclasses import dataclass, field


@dataclass
class CampusGraph:
    """
    A weighted graph of campus locations.

    Each edge represents a connection between two locations.
    Edge weights can represent distance or estimated travel time.
    """
    adjacency: dict[str, dict[str, float]] = field(default_factory=dict)

    def add_location(self, location_id: str) -> None:
        if not location_id:
            raise ValueError("Location ID cannot be empty")

        self.adjacency.setdefault(location_id, {})

    def add_connection(
        self,
        source: str,
        destination: str,
        weight: float,
        bidirectional: bool = True,
    ) -> None:
        if not source or not destination:
            raise ValueError("Location IDs cannot be empty")

        if source == destination:
            raise ValueError("A location cannot connect to itself")

        if weight <= 0:
            raise ValueError("Connection weight must be positive")

        self.add_location(source)
        self.add_location(destination)

        self.adjacency[source][destination] = weight

        if bidirectional:
            self.adjacency[destination][source] = weight

    def get_neighbors(self, location_id: str) -> dict[str, float]:
        if location_id not in self.adjacency:
            raise ValueError(f"Unknown location: {location_id}")

        return self.adjacency[location_id].copy()

    def has_location(self, location_id: str) -> bool:
        return location_id in self.adjacency
