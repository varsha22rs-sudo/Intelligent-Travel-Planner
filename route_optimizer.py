"""Destination-order optimization for the Intelligent Travel Planner.

The first location is the fixed starting point. Every other supplied location
is visited exactly once. This module reorders the locations provided by the
user; it does not add unrequested intermediate destinations.

Expected inputs:
    locations = [{"name": "Delhi"}, {"name": "Agra"}, {"name": "Jaipur"}]
    leg_options = {
        ("Delhi", "Agra"): [
            {"cost": 500, "hours": 3, "distance_km": 220, "mode": "Train"}
        ]
    }

Supported algorithms: BFS, DFS, UCS, Greedy, A*
Supported metrics: cost, time, hours
"""

import heapq
from collections import deque
from itertools import count
from math import inf


ALGORITHMS = ("BFS", "DFS", "UCS", "Greedy", "A*")


def _metric_key(metric):
    """Return the field name used for the requested optimization metric."""
    if metric == "cost":
        return "cost"
    if metric in ("time", "hours"):
        return "hours"
    raise ValueError("Metric must be 'cost' or 'time'.")


def _best_option(options, metric):
    """Choose the cheapest or quickest available transport option for a leg."""
    key = _metric_key(metric)
    valid_options = []

    for option in options:
        try:
            value = float(option[key])
        except (KeyError, TypeError, ValueError):
            continue

        if value >= 0:
            valid_options.append((value, option))

    if not valid_options:
        return None

    return dict(min(valid_options, key=lambda item: item[0])[1])


def _edge_weight(source, destination, leg_options, metric):
    """Return the best available weight for a leg, or infinity if unavailable."""
    option = _best_option(leg_options.get((source, destination), []), metric)
    if option is None:
        return inf
    return float(option[_metric_key(metric)])


def _heuristic(current, remaining, leg_options, metric):
    """Estimate a lower bound for visiting all remaining destinations."""
    if not remaining:
        return 0.0

    connection_weights = [
        _edge_weight(current, city, leg_options, metric)
        for city in remaining
    ]
    finite_weights = [weight for weight in connection_weights if weight < inf]

    if not finite_weights:
        # A zero heuristic is safe when a direct connection is unavailable.
        return 0.0

    connection_cost = min(finite_weights)

    if len(remaining) == 1:
        return connection_cost

    # Minimum spanning tree lower bound among the remaining destinations.
    tree_nodes = {remaining[0]}
    outside = set(remaining[1:])
    tree_cost = 0.0

    while outside:
        best_weight = inf
        best_node = None

        for left in tree_nodes:
            for right in outside:
                # Use the cheaper direction as a lower-bound edge weight.
                weight = min(
                    _edge_weight(left, right, leg_options, metric),
                    _edge_weight(right, left, leg_options, metric),
                )
                if weight < best_weight:
                    best_weight = weight
                    best_node = right

        if best_node is None or best_weight == inf:
            # Keep the heuristic conservative if the pairwise data is incomplete.
            return connection_cost

        tree_cost += best_weight
        tree_nodes.add(best_node)
        outside.remove(best_node)

    return connection_cost + tree_cost


def optimize_visit_order(locations, leg_options, algorithm="A*", metric="cost"):
    """Optimize the order of supplied destinations while keeping the start fixed.

    Args:
        locations: List of dictionaries with a "name" key. The first is the start.
        leg_options: Mapping of (from_name, to_name) to transport-option lists.
        algorithm: BFS, DFS, UCS, Greedy, or A*.
        metric: "cost", "time", or "hours".

    Returns:
        A dictionary containing the visit path, selected legs, totals, and
        algorithm details.
    """
    if algorithm not in ALGORITHMS:
        raise ValueError(
            f"Unknown algorithm. Choose one of: {', '.join(ALGORITHMS)}"
        )

    metric_key = _metric_key(metric)

    if not locations or len(locations) < 2:
        raise ValueError("Provide a starting location and at least one destination.")

    try:
        names = [str(item["name"]).strip() for item in locations]
    except (TypeError, KeyError):
        raise ValueError("Each location must be a dictionary with a 'name' field.")

    if any(not name for name in names):
        raise ValueError("Location names cannot be empty.")

    if len(set(names)) != len(names):
        raise ValueError("The starting location and destinations must be unique.")

    start = names[0]
    destinations = names[1:]
    destination_indexes = {name: index for index, name in enumerate(destinations)}
    full_mask = (1 << len(destinations)) - 1

    # State format: (current location, visited bitmask, path, selected legs).
    serial = count()
    start_state = (start, 0, [start], [])
    best_cost = {(start, 0): 0.0}

    if algorithm == "BFS":
        frontier = deque([(0, next(serial), start_state)])
    elif algorithm == "DFS":
        frontier = [(0, next(serial), start_state)]
    else:
        initial_priority = (
            _heuristic(start, destinations, leg_options, metric)
            if algorithm in ("Greedy", "A*")
            else 0.0
        )
        frontier = [(initial_priority, next(serial), start_state)]
        heapq.heapify(frontier)

    while frontier:
        if algorithm == "DFS":
            _, _, state = frontier.pop()
        elif algorithm == "BFS":
            _, _, state = frontier.popleft()
        else:
            _, _, state = heapq.heappop(frontier)

        current, mask, path, selected_legs = state
        current_cost = sum(float(leg[metric_key]) for leg in selected_legs)
        state_key = (current, mask)

        if algorithm in ("UCS", "A*") and current_cost > best_cost.get(state_key, inf):
            continue

        if mask == full_mask:
            return {
                "path": path,
                "legs": selected_legs,
                "algorithm": algorithm,
                "optimized_metric": "cost" if metric_key == "cost" else "time",
                "optimized_value": round(current_cost, 2),
                "total_cost": round(
                    sum(float(leg["cost"]) for leg in selected_legs), 2
                ),
                "total_hours": round(
                    sum(float(leg["hours"]) for leg in selected_legs), 2
                ),
                "total_distance_km": round(
                    sum(float(leg.get("distance_km", 0)) for leg in selected_legs), 2
                ),
            }

        unvisited = [
            city
            for index, city in enumerate(destinations)
            if not (mask & (1 << index))
        ]

        # Reverse DFS expansion order for predictable traversal.
        if algorithm == "DFS":
            unvisited.reverse()

        for city in unvisited:
            option = _best_option(leg_options.get((current, city), []), metric)
            if option is None:
                continue

            new_mask = mask | (1 << destination_indexes[city])
            new_cost = current_cost + float(option[metric_key])
            new_key = (city, new_mask)

            if algorithm in ("UCS", "A*"):
                if new_cost >= best_cost.get(new_key, inf):
                    continue
                best_cost[new_key] = new_cost

            new_path = path + [city]
            new_legs = selected_legs + [dict(option)]
            new_state = (city, new_mask, new_path, new_legs)

            if algorithm in ("BFS", "DFS"):
                frontier.append((0, next(serial), new_state))
            elif algorithm == "Greedy":
                remaining_after = [
                    other
                    for index, other in enumerate(destinations)
                    if not (new_mask & (1 << index))
                ]
                priority = _heuristic(city, remaining_after, leg_options, metric)
                heapq.heappush(frontier, (priority, next(serial), new_state))
            elif algorithm == "UCS":
                heapq.heappush(frontier, (new_cost, next(serial), new_state))
            else:  # A*
                remaining_after = [
                    other
                    for index, other in enumerate(destinations)
                    if not (new_mask & (1 << index))
                ]
                heuristic_cost = _heuristic(
                    city, remaining_after, leg_options, metric
                )
                heapq.heappush(
                    frontier,
                    (new_cost + heuristic_cost, next(serial), new_state),
                )

    raise ValueError(
        "No complete route could visit every destination with the available "
        "transport estimates. Try fewer destinations or different transport modes."
    )
