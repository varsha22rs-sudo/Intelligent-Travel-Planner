
from route_optimizer import optimize_visit_order

locations = [
    {"name": "Start"},
    {"name": "A"},
    {"name": "B"},
    {"name": "C"},
]

leg_options = {
    ("Start", "A"): [
        {"cost": 10, "hours": 5, "distance_km": 10, "mode": "Car"}
    ],
    ("Start", "B"): [
        {"cost": 2, "hours": 2, "distance_km": 20, "mode": "Train"}
    ],
    ("Start", "C"): [
        {"cost": 20, "hours": 8, "distance_km": 30, "mode": "Car"}
    ],
    ("A", "B"): [
        {"cost": 2, "hours": 1, "distance_km": 5, "mode": "Car"}
    ],
    ("A", "C"): [
        {"cost": 3, "hours": 2, "distance_km": 8, "mode": "Car"}
    ],
    ("B", "A"): [
        {"cost": 2, "hours": 1, "distance_km": 5, "mode": "Car"}
    ],
    ("B", "C"): [
        {"cost": 2, "hours": 1, "distance_km": 5, "mode": "Car"}
    ],
    ("C", "A"): [
        {"cost": 3, "hours": 2, "distance_km": 8, "mode": "Car"}
    ],
    ("C", "B"): [
        {"cost": 2, "hours": 1, "distance_km": 5, "mode": "Car"}
    ],
}

for algorithm in ["BFS", "DFS", "UCS", "Greedy", "A*"]:
    result = optimize_visit_order(
        locations,
        leg_options,
        algorithm=algorithm,
        metric="cost",
    )

    print(
        algorithm,
        "->",
        " -> ".join(result["path"]),
        "| Total cost:",
        result["total_cost"],
        "| Total hours:",
        result["total_hours"],
        "| Optimized value:",
        result["optimized_value"],
    )
