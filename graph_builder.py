
"""Graph builders for sample and dynamically resolved travel locations."""

import networkx as nx
from knowledge_base import CITIES, ROUTES


def build_graph(allowed_transport=None):
    """Build a graph from the sample Uttarakhand knowledge base."""

    graph = nx.Graph()

    for city, details in CITIES.items():
        graph.add_node(city, **details)

    allowed = set(allowed_transport or [])

    for route in ROUTES:
        if allowed and route["transport"] not in allowed:
            continue

        graph.add_edge(
            route["from"],
            route["to"],
            transport=route["transport"],
            cost=float(route["cost"]),
            time=float(route["time"]),
            distance=float(route["distance"]),
        )

    return graph


def build_dynamic_graph(locations, leg_records):
    """Build a graph from dynamically resolved locations and travel legs."""

    graph = nx.Graph()

    # Add all locations, even if a route is not available for one of them.
    for loc in locations:
        graph.add_node(
            loc["name"],
            lat=float(loc["latitude"]),
            lon=float(loc["longitude"]),
            type="dynamic location",
        )

    # Add only valid edges whose endpoints exist in the graph.
    for leg in leg_records:
        source = leg["from"]
        destination = leg["to"]

        if source not in graph or destination not in graph:
            continue

        graph.add_edge(
            source,
            destination,
            transport=leg["mode"],
            cost=float(leg["cost"]),
            time=float(leg["hours"]),
            distance=float(leg["distance_km"]),
        )

    return graph
