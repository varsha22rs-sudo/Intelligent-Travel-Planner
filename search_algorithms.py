"""Educational implementations of BFS, DFS, UCS, Greedy Best-First Search and A*."""
from collections import deque
import heapq
import math


def _edge_weight(graph, a, b, metric):
    return float(graph[a][b].get(metric, 1))


def _path_cost(graph, path, metric):
    return sum(_edge_weight(graph, path[i], path[i + 1], metric) for i in range(len(path) - 1))


def _heuristic(graph, city, goal, metric):
    """Straight-line-distance heuristic scaled conservatively for cost or time."""
    a = graph.nodes[city]
    b = graph.nodes[goal]
    lat1, lon1 = math.radians(a.get("lat", 0)), math.radians(a.get("lon", 0))
    lat2, lon2 = math.radians(b.get("lat", 0)), math.radians(b.get("lon", 0))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    hav = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    straight_km = 6371 * 2 * math.asin(min(1, math.sqrt(hav)))

    # Minimum observed edge weight per kilometre; avoids overestimating based on
    # the sample edge data as far as this simple model permits.
    ratios = []
    for u, v, data in graph.edges(data=True):
        distance = data.get("distance", 0)
        weight = data.get(metric, 0)
        if distance > 0 and weight >= 0:
            ratios.append(weight / distance)
    scale = min(ratios) if ratios else 0
    return straight_km * scale


def bfs(graph, start, goal):
    """Breadth-first search: minimizes number of edges, not cost or time."""
    if start not in graph or goal not in graph:
        return None
    queue = deque([(start, [start])])
    visited = {start}
    while queue:
        node, path = queue.popleft()
        if node == goal:
            return {"path": path, "cost": _path_cost(graph, path, "cost"),
                    "time": _path_cost(graph, path, "time"), "algorithm": "BFS"}
        for neighbour in graph.neighbors(node):
            if neighbour not in visited:
                visited.add(neighbour)
                queue.append((neighbour, path + [neighbour]))
    return None


def dfs(graph, start, goal):
    """Depth-first search: explores deeply before backtracking."""
    if start not in graph or goal not in graph:
        return None
    stack = [(start, [start])]
    visited = set()
    while stack:
        node, path = stack.pop()
        if node == goal:
            return {"path": path, "cost": _path_cost(graph, path, "cost"),
                    "time": _path_cost(graph, path, "time"), "algorithm": "DFS"}
        if node in visited:
            continue
        visited.add(node)
        for neighbour in sorted(graph.neighbors(node), reverse=True):
            if neighbour not in visited:
                stack.append((neighbour, path + [neighbour]))
    return None


def ucs(graph, start, goal, metric="cost"):
    """Uniform Cost Search: returns the least-cost path for the selected metric."""
    if start not in graph or goal not in graph:
        return None
    frontier = [(0.0, start, [start])]
    best = {start: 0.0}
    while frontier:
        cost_so_far, node, path = heapq.heappop(frontier)
        if cost_so_far != best.get(node):
            continue
        if node == goal:
            return {"path": path, "cost": _path_cost(graph, path, "cost"),
                    "time": _path_cost(graph, path, "time"), "algorithm": "UCS",
                    "optimized_metric": metric, "optimized_value": cost_so_far}
        for neighbour in graph.neighbors(node):
            new_cost = cost_so_far + _edge_weight(graph, node, neighbour, metric)
            if new_cost < best.get(neighbour, float("inf")):
                best[neighbour] = new_cost
                heapq.heappush(frontier, (new_cost, neighbour, path + [neighbour]))
    return None


def greedy_best_first(graph, start, goal, metric="cost"):
    """Greedy search selects the frontier city with the smallest heuristic."""
    if start not in graph or goal not in graph:
        return None
    frontier = [(_heuristic(graph, start, goal, metric), 0.0, start, [start])]
    visited = set()
    while frontier:
        _, accumulated, node, path = heapq.heappop(frontier)
        if node == goal:
            return {"path": path, "cost": _path_cost(graph, path, "cost"),
                    "time": _path_cost(graph, path, "time"), "algorithm": "Greedy",
                    "optimized_metric": metric, "optimized_value": accumulated}
        if node in visited:
            continue
        visited.add(node)
        for neighbour in graph.neighbors(node):
            if neighbour not in visited:
                accumulated_new = accumulated + _edge_weight(graph, node, neighbour, metric)
                heapq.heappush(frontier, (_heuristic(graph, neighbour, goal, metric),
                                          accumulated_new, neighbour, path + [neighbour]))
    return None


def astar(graph, start, goal, metric="cost"):
    """A*: ranks frontier paths by g(n) + h(n)."""
    if start not in graph or goal not in graph:
        return None
    frontier = [(_heuristic(graph, start, goal, metric), 0.0, start, [start])]
    best = {start: 0.0}
    while frontier:
        _, g_score, node, path = heapq.heappop(frontier)
        if g_score != best.get(node):
            continue
        if node == goal:
            return {"path": path, "cost": _path_cost(graph, path, "cost"),
                    "time": _path_cost(graph, path, "time"), "algorithm": "A*",
                    "optimized_metric": metric, "optimized_value": g_score}
        for neighbour in graph.neighbors(node):
            new_g = g_score + _edge_weight(graph, node, neighbour, metric)
            if new_g < best.get(neighbour, float("inf")):
                best[neighbour] = new_g
                f_score = new_g + _heuristic(graph, neighbour, goal, metric)
                heapq.heappush(frontier, (f_score, new_g, neighbour, path + [neighbour]))
    return None



def find_route(graph, start, goal, algorithm="A*", metric="cost"):
    """Common entry point for the route-search algorithms."""

    algorithms = {
        "BFS": lambda: bfs(graph, start, goal),
        "DFS": lambda: dfs(graph, start, goal),
        "UCS": lambda: ucs(graph, start, goal, metric),
        "Greedy": lambda: greedy_best_first(graph, start, goal, metric),
        "A*": lambda: astar(graph, start, goal, metric),
    }

    if algorithm not in algorithms:
        raise ValueError(
            f"Unknown algorithm: {algorithm}. "
            f"Choose one of: {', '.join(algorithms.keys())}"
        )

    if metric not in ("cost", "time"):
        raise ValueError("Metric must be either 'cost' or 'time'.")

    return algorithms[algorithm]()
