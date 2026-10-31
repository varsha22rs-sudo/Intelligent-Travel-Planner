
from route_optimizer import optimize_visit_order

locations = [
    {"name": "Start"},
    {"name": "A"},
    {"name": "B"},
    {"name": "C"},
]

leg_options = {
    ("Start", "A"): [
        {"cost": 8, "hours": 4, "distance_km": 20, "mode": "Car"}
    ],
    ("Start", "B"): [
        {"cost": 3, "hours": 2, "distance_km": 15, "mode": "Train"}
    ],
    ("Start", "C"): [
        {"cost": 7, "hours": 3, "distance_km": 18, "mode": "Car"}
    ],
    ("A", "B"): [
        {"cost": 2, "hours": 1, "distance_km": 5, "mode": "Car"}
    ],
    ("A", "C"): [
        {"cost": 2, "hours": 1, "distance_km": 6, "mode": "Car"}
    ],
    ("B", "A"): [
        {"cost": 2, "hours": 1, "distance_km": 5, "mode": "Car"}
    ],
    ("B", "C"): [
        {"cost": 2, "hours": 1, "distance_km": 5, "mode": "Car"}
    ],
    ("C", "A"): [
        {"cost": 2, "hours": 1, "distance_km": 6, "mode": "Car"}
    ],
    ("C", "B"): [
        {"cost": 2, "hours": 1, "distance_km": 5, "mode": "Car"}
    ],
}

for metric in ["cost", "time"]:
    ucs = optimize_visit_order(
        locations, leg_options, algorithm="UCS", metric=metric
    )
    astar = optimize_visit_order(
        locations, leg_options, algorithm="A*", metric=metric
    )

    print(f"\nMetric: {metric}")
    print("UCS:", ucs["path"], "| Value:", ucs["optimized_value"])
    print("A* :", astar["path"], "| Value:", astar["optimized_value"])

    if ucs["optimized_value"] == astar["optimized_value"]:
        print("PASS: UCS and A* agree on the optimal value.")
    else:
        print("CHECK: UCS and A* returned different values.")
