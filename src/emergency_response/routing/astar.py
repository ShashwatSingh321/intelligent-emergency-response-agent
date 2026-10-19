
import heapq
from itertools import count
from math import inf

from emergency_response.routing.graph import CampusGraph


def astar(
    graph: CampusGraph,
    start: str,
    goal: str,
    heuristic: dict[str, float] | None = None,
) -> tuple[list[str], float]:
    """
    Find a minimum-cost route using A*.

    The heuristic maps each location to an estimated remaining cost.
    Use an admissible heuristic (never overestimating the true cost)
    to guarantee an optimal route.

    Returns (route, total_cost).
    If no route exists, returns ([], infinity).
    """
    if not graph.has_location(start):
        raise ValueError(f"Unknown start location: {start}")

    if not graph.has_location(goal):
        raise ValueError(f"Unknown goal location: {goal}")

    estimates = heuristic or {}

    for location, estimate in estimates.items():
        if not graph.has_location(location):
            raise ValueError(f"Unknown heuristic location: {location}")
        if estimate < 0 or estimate == inf:
            raise ValueError("Heuristic estimates must be finite and non-negative")

    if start == goal:
        return [start], 0.0

    distances = {location: inf for location in graph.adjacency}
    previous: dict[str, str] = {}
    distances[start] = 0.0

    sequence = count()
    priority_queue = [
        (estimates.get(start, 0.0), next(sequence), 0.0, start)
    ]

    while priority_queue:
        _, _, current_distance, current = heapq.heappop(priority_queue)

        if current_distance > distances[current]:
            continue

        if current == goal:
            break

        for neighbor, weight in graph.get_neighbors(current).items():
            new_distance = current_distance + weight

            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                previous[neighbor] = current

                estimated_total = new_distance + estimates.get(neighbor, 0.0)
                heapq.heappush(
                    priority_queue,
                    (
                        estimated_total,
                        next(sequence),
                        new_distance,
                        neighbor,
                    ),
                )

    if distances[goal] == inf:
        return [], inf

    route = []
    current = goal

    while current != start:
        route.append(current)
        current = previous[current]

    route.append(start)
    route.reverse()

    return route, distances[goal]
