
from math import inf

from emergency_response.models.ambulance import Ambulance, AmbulanceStatus
from emergency_response.models.emergency import EmergencyReport
from emergency_response.routing.graph import CampusGraph
from emergency_response.services.dispatch_service import (
    select_ambulance_by_route,
)


def make_graph():
    graph = CampusGraph()
    graph.add_connection("HOSTEL", "LIBRARY", 8)
    graph.add_connection("GATE", "LIBRARY", 2)
    graph.add_connection("GATE", "HOSTEL", 3)
    return graph


def make_report(people_affected=1, location_id="LIBRARY"):
    return EmergencyReport(
        id="ER-301",
        description="A student needs medical assistance",
        location_id=location_id,
        people_affected=people_affected,
    )


def test_selects_ambulance_with_lowest_route_cost():
    graph = make_graph()
    ambulances = [
        Ambulance(
            id="AMB-01",
            current_location_id="HOSTEL",
            equipment={"first_aid"},
        ),
        Ambulance(
            id="AMB-02",
            current_location_id="GATE",
            equipment={"first_aid"},
        ),
    ]

    ambulance, route, cost = select_ambulance_by_route(
        make_report(), ambulances, graph, {"first_aid"}
    )

    assert ambulance is not None
    assert ambulance.id == "AMB-02"
    assert route == ["GATE", "LIBRARY"]
    assert cost == 2


def test_ignores_unavailable_ambulance():
    graph = make_graph()
    ambulances = [
        Ambulance(
            id="AMB-01",
            current_location_id="GATE",
            status=AmbulanceStatus.BUSY,
            equipment={"first_aid"},
        )
    ]

    ambulance, route, cost = select_ambulance_by_route(
        make_report(), ambulances, graph, {"first_aid"}
    )

    assert ambulance is None
    assert route == []
    assert cost == inf


def test_ignores_ambulance_without_required_equipment():
    graph = make_graph()
    ambulances = [
        Ambulance(
            id="AMB-01",
            current_location_id="GATE",
            equipment={"first_aid"},
        )
    ]

    ambulance, route, cost = select_ambulance_by_route(
        make_report(), ambulances, graph, {"oxygen"}
    )

    assert ambulance is None
    assert route == []
    assert cost == inf


def test_ignores_ambulance_with_no_route():
    graph = CampusGraph()
    graph.add_location("LIBRARY")
    graph.add_location("ISOLATED_HOSTEL")

    ambulances = [
        Ambulance(
            id="AMB-01",
            current_location_id="ISOLATED_HOSTEL",
            equipment={"first_aid"},
        )
    ]

    ambulance, route, cost = select_ambulance_by_route(
        make_report(), ambulances, graph, {"first_aid"}
    )

    assert ambulance is None
    assert route == []
    assert cost == inf


def test_selects_none_when_no_ambulances_are_provided():
    ambulance, route, cost = select_ambulance_by_route(
        make_report(), [], make_graph()
    )

    assert ambulance is None
    assert route == []
    assert cost == inf


def test_ignores_ambulance_with_insufficient_capacity():
    graph = make_graph()
    ambulances = [
        Ambulance(
            id="AMB-01",
            current_location_id="GATE",
            equipment={"first_aid"},
            capacity=1,
        )
    ]

    ambulance, route, cost = select_ambulance_by_route(
        make_report(people_affected=3),
        ambulances,
        graph,
        {"first_aid"},
    )

    assert ambulance is None
    assert route == []
    assert cost == inf


def test_selects_alphabetically_first_id_when_route_costs_tie():
    graph = make_graph()
    ambulances = [
        Ambulance(
            id="AMB-02",
            current_location_id="GATE",
            equipment={"first_aid"},
        ),
        Ambulance(
            id="AMB-01",
            current_location_id="GATE",
            equipment={"first_aid"},
        ),
    ]

    ambulance, route, cost = select_ambulance_by_route(
        make_report(), ambulances, graph, {"first_aid"}
    )

    assert ambulance is not None
    assert ambulance.id == "AMB-01"
    assert route == ["GATE", "LIBRARY"]
    assert cost == 2


def test_same_location_has_zero_route_cost():
    graph = make_graph()
    ambulances = [
        Ambulance(
            id="AMB-01",
            current_location_id="LIBRARY",
            equipment={"first_aid"},
        )
    ]

    ambulance, route, cost = select_ambulance_by_route(
        make_report(), ambulances, graph, {"first_aid"}
    )

    assert ambulance is not None
    assert ambulance.id == "AMB-01"
    assert route == ["LIBRARY"]
    assert cost == 0


def test_ignores_ambulance_at_unknown_location():
    graph = make_graph()
    ambulances = [
        Ambulance(
            id="AMB-01",
            current_location_id="UNKNOWN",
            equipment={"first_aid"},
        )
    ]

    ambulance, route, cost = select_ambulance_by_route(
        make_report(), ambulances, graph, {"first_aid"}
    )

    assert ambulance is None
    assert route == []
    assert cost == inf


def test_ignores_report_at_unknown_location():
    graph = make_graph()
    report = make_report(location_id="UNKNOWN")

    ambulances = [
        Ambulance(
            id="AMB-01",
            current_location_id="GATE",
            equipment={"first_aid"},
        )
    ]

    ambulance, route, cost = select_ambulance_by_route(
        report, ambulances, graph, {"first_aid"}
    )

    assert ambulance is None
    assert route == []
    assert cost == inf
