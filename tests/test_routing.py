
import pytest
from emergency_response.routing.astar import astar
from emergency_response.routing.graph import CampusGraph


def test_add_location():
    graph = CampusGraph()
    graph.add_location("LIBRARY")

    assert graph.has_location("LIBRARY")


def test_add_bidirectional_connection():
    graph = CampusGraph()
    graph.add_connection("LIBRARY", "HOSTEL", 2.5)

    assert graph.get_neighbors("LIBRARY") == {"HOSTEL": 2.5}
    assert graph.get_neighbors("HOSTEL") == {"LIBRARY": 2.5}


def test_add_one_way_connection():
    graph = CampusGraph()
    graph.add_connection(
        "GATE",
        "LIBRARY",
        1.0,
        bidirectional=False,
    )

    assert graph.get_neighbors("GATE") == {"LIBRARY": 1.0}
    assert graph.get_neighbors("LIBRARY") == {}


def test_rejects_non_positive_weight():
    graph = CampusGraph()

    with pytest.raises(ValueError):
        graph.add_connection("LIBRARY", "HOSTEL", 0)


def test_rejects_connection_to_same_location():
    graph = CampusGraph()

    with pytest.raises(ValueError):
        graph.add_connection("LIBRARY", "LIBRARY", 1)


def test_unknown_location_raises_error():
    graph = CampusGraph()

    with pytest.raises(ValueError):
        graph.get_neighbors("UNKNOWN")



from math import inf

from emergency_response.routing.dijkstra import dijkstra


def make_sample_graph():
    graph = CampusGraph()
    graph.add_connection("LIBRARY", "HOSTEL", 4)
    graph.add_connection("LIBRARY", "AUDITORIUM", 2)
    graph.add_connection("AUDITORIUM", "HOSTEL", 1)
    graph.add_connection("HOSTEL", "GATE", 3)
    graph.add_connection("AUDITORIUM", "GATE", 7)
    return graph


def test_dijkstra_finds_lowest_cost_route():
    graph = make_sample_graph()

    route, cost = dijkstra(graph, "LIBRARY", "GATE")

    assert route == ["LIBRARY", "AUDITORIUM", "HOSTEL", "GATE"]
    assert cost == 6


def test_dijkstra_handles_same_start_and_goal():
    graph = make_sample_graph()

    route, cost = dijkstra(graph, "LIBRARY", "LIBRARY")

    assert route == ["LIBRARY"]
    assert cost == 0


def test_dijkstra_returns_infinity_when_no_route_exists():
    graph = CampusGraph()
    graph.add_location("LIBRARY")
    graph.add_location("HOSTEL")

    route, cost = dijkstra(graph, "LIBRARY", "HOSTEL")

    assert route == []
    assert cost == inf


def test_dijkstra_rejects_unknown_location():
    graph = make_sample_graph()

    with pytest.raises(ValueError):
        dijkstra(graph, "UNKNOWN", "GATE")




def test_astar_finds_lowest_cost_route():
    graph = make_sample_graph()

    route, cost = astar(graph, "LIBRARY", "GATE")

    assert route == ["LIBRARY", "AUDITORIUM", "HOSTEL", "GATE"]
    assert cost == 6


def test_astar_with_admissible_heuristic():
    graph = make_sample_graph()
    heuristic = {
        "LIBRARY": 5,
        "AUDITORIUM": 4,
        "HOSTEL": 3,
        "GATE": 0,
    }

    route, cost = astar(
        graph,
        "LIBRARY",
        "GATE",
        heuristic,
    )

    assert route == ["LIBRARY", "AUDITORIUM", "HOSTEL", "GATE"]
    assert cost == 6


def test_astar_returns_infinity_when_no_route_exists():
    graph = CampusGraph()
    graph.add_location("LIBRARY")
    graph.add_location("HOSTEL")

    route, cost = astar(graph, "LIBRARY", "HOSTEL")

    assert route == []
    assert cost == inf


def test_astar_rejects_unknown_locations():
    graph = make_sample_graph()

    with pytest.raises(ValueError):
        astar(graph, "UNKNOWN", "GATE")


