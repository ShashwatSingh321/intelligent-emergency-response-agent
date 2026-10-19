
import heapq
from math import inf

from emergency_response.routing.graph import CampusGraph


def dijkstra(
    graph: CampusGraph,
    start: str,
    goal: str,
) -> tuple[list[str], float]:
    """
    Find the minimum-cost route from start to goal.

    Returns (route, total_cost).
    If no route exists, returns ([], infinity).
    """
    if not graph.has_location(start):
        raise ValueError(f"Unknown start location: {start}")

    if not graph.has_location(goal):
        raise ValueError(f"Unknown goal location: {goal}")

    if start == goal:
        return [start], 0.0

    distances = {location: inf for location in graph.adjacency}
    previous: dict[str, str] = {}
    distances[start] = 0.0

    priority_queue = [(0.0, start)]

    while priority_queue:
        current_distance, current = heapq.heappop(priority_queue)

        if current_distance > distances[current]:
            continue

        if current == goal:
            break

        for neighbor, weight in graph.get_neighbors(current).items():
            new_distance = current_distance + weight

            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                previous[neighbor] = current
                heapq.heappush(
                    priority_queue,
                    (new_distance, neighbor),
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
