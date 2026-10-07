"""Open TSP: fixed garage, student pickups, fixed IFCE destination.

Coordinates are synthetic kilometres, speed is 40 km/h, service is 1 minute.
Departure is 17:50 and the arrival deadline is 19:00 (70 minutes).
"""
from pathlib import Path
import csv
import math
import time

import networkx as nx
import pulp as pl

DATA = Path(__file__).resolve().parents[1] / "data"


def load_instance(students=5, windows=False, impossible=False):
    if not 1 <= students <= 30:
        raise ValueError("Choose 1 to 30 students")
    with (DATA / "van_stops.csv").open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    selected = [rows[0], *rows[1:students + 1], rows[-1]]
    graph = nx.DiGraph()
    for row in selected:
        graph.add_node(row["stop"], x=float(row["x_km"]), y=float(row["y_km"]))
    for i in graph:
        for j in graph:
            if i != j:
                a, b = graph.nodes[i], graph.nodes[j]
                km = round(math.hypot(a["x"] - b["x"], a["y"] - b["y"]), 4)
                graph.add_edge(i, j, km=km, minutes=km * 1.5)
    pupils = [row["stop"] for row in selected[1:-1]]
    earliest = {p: 0.0 for p in pupils}
    if windows:
        for p in pupils[:3]:
            earliest[p] = 80.0 if impossible else 40.0  # 19:10 or 18:30
    return dict(graph=graph, students=pupils, start="garagem", end="IFCE",
                earliest=earliest, windows=windows, deadline=70.0)


def evaluate_route(instance, route, traffic_factor=1.0):
    if not math.isfinite(traffic_factor) or traffic_factor <= 0:
        raise ValueError("Traffic factor must be positive and finite")
    expected = [instance["start"], *instance["students"], instance["end"]]
    if (not route or route[0] != expected[0] or route[-1] != expected[-1]
            or sorted(route) != sorted(expected)):
        return dict(feasible=False, reason="Missing, repeated or misplaced stops")
    clock, distance, lateness = 0.0, 0.0, 0.0
    arrivals = []
    for i, j in zip(route, route[1:]):
        edge = instance["graph"][i][j]
        distance += edge["km"]
        clock += edge["minutes"] * traffic_factor
        clock = max(clock, instance["earliest"].get(j, 0.0))
        deadline = instance["deadline"] if j == instance["end"] else 65.0
        # Intermediate latest times only apply to the time-window model.
        if instance["windows"] or j == instance["end"]:
            lateness += max(0.0, clock - deadline)
        arrivals.append(dict(stop=j, arrival_minutes=round(clock, 4)))
        if j != instance["end"]:
            clock += 1.0
    return dict(feasible=lateness <= 1e-6, km=round(distance, 4),
                arrival_minutes=round(clock, 4), lateness_minutes=round(lateness, 4),
                arrivals=arrivals)


def build_model(instance, relax=False):
    graph, pupils = instance["graph"], instance["students"]
    start, end, n = instance["start"], instance["end"], len(pupils)
    arcs = [(i, j) for i in [start, *pupils] for j in [*pupils, end] if i != j]
    model = pl.LpProblem("van_open_tsp", pl.LpMinimize)
    x = pl.LpVariable.dicts("arc", arcs, 0, 1, cat="Continuous" if relax else "Binary")
    model += pl.lpSum(graph[i][j]["km"] * x[i, j] for i, j in arcs)
    for i in [start, *pupils]:
        model += pl.lpSum(x[a, b] for a, b in arcs if a == i) == 1
    for j in [*pupils, end]:
        model += pl.lpSum(x[a, b] for a, b in arcs if b == j) == 1
    # MTZ: prevent disconnected cycles among the student stops.
    order = pl.LpVariable.dicts("visit_order", pupils, 1, n)
    for i in pupils:
        for j in pupils:
            if i != j:
                model += order[i] - order[j] + n * x[i, j] <= n - 1
    model += pl.lpSum(graph[i][j]["minutes"] * x[i, j] for i, j in arcs) + n <= instance["deadline"]
    if instance["windows"]:
        arrival = pl.LpVariable.dicts("arrival", list(graph), 0, 90)
        model += arrival[start] == 0
        model += arrival[end] <= instance["deadline"]
        for p in pupils:
            model += arrival[p] >= instance["earliest"][p]
            model += arrival[p] <= 65
        for i, j in arcs:
            service = 0 if i == start else 1
            model += arrival[j] >= arrival[i] + service + graph[i][j]["minutes"] - 180 * (1 - x[i, j])
    return model, x


def solve_route(instance, time_limit=5, relax=False):
    if not math.isfinite(time_limit) or time_limit <= 0:
        raise ValueError("Time limit must be positive and finite")
    model, x = build_model(instance, relax)
    started = time.perf_counter()
    model.solve(pl.PULP_CBC_CMD(msg=False, timeLimit=time_limit))
    elapsed = time.perf_counter() - started
    certified = model.status == pl.LpStatusOptimal and model.sol_status == pl.LpSolutionOptimal
    result = dict(solver_status=pl.LpStatus[model.status], seconds=round(elapsed, 4),
                  certified_optimal=certified, route=None, feasible=False)
    if relax:
        result.update(status="LP optimal" if certified else "LP unfinished",
                      lower_bound_km=pl.value(model.objective) if certified else None)
        return result
    values = [var.value() for var in x.values()]
    if (model.status != pl.LpStatusInfeasible and all(v is not None for v in values)
            and all(abs(v - round(v)) < 1e-5 for v in values)):
        successor = {i: j for (i, j), var in x.items() if var.value() > .5}
        route = [instance["start"]]
        while route[-1] in successor and len(route) <= len(instance["students"]) + 1:
            nxt = successor[route[-1]]
            if nxt in route:
                break
            route.append(nxt)
        audit = evaluate_route(instance, route)
        if audit["feasible"]:
            result.update(audit, route=route)
    result["status"] = ("Optimal" if certified and result["feasible"] else
                        "Feasible, proof unfinished" if result["feasible"] else
                        "Infeasible" if model.status == pl.LpStatusInfeasible else
                        "No feasible route returned")
    return result


def heuristic_route(instance, time_limit=5):
    if not math.isfinite(time_limit) or time_limit <= 0:
        raise ValueError("Time limit must be positive and finite")
    started = time.perf_counter()
    remaining, route = set(instance["students"]), [instance["start"]]
    while remaining:
        nxt = min(remaining, key=lambda p: (instance["graph"][route[-1]][p]["km"], p))
        route.append(nxt)
        remaining.remove(nxt)
    route.append(instance["end"])
    initial = evaluate_route(instance, route)
    def score(candidate):
        audit = evaluate_route(instance, candidate)
        return audit["lateness_minutes"], audit["km"]
    improved = True
    while improved and time.perf_counter() - started < time_limit:
        improved, best = False, score(route)
        for i in range(1, len(route) - 2):
            for j in range(i + 1, len(route) - 1):
                if time.perf_counter() - started >= time_limit:
                    break
                candidate = route[:i] + list(reversed(route[i:j + 1])) + route[j + 1:]
                candidate_score = score(candidate)
                if candidate_score < best:
                    route, best, improved = candidate, candidate_score, True
    audit = evaluate_route(instance, route)
    return dict(audit, route=route, nearest_neighbor_km=initial["km"],
                status="Heuristic candidate", certified_optimal=False,
                seconds=round(time.perf_counter() - started, 4))
