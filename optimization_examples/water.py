"""Crop planning with synthetic hectares, water, capital and profit coefficients."""
from pathlib import Path
import csv
import pulp as pl


def load_crops():
    path = Path(__file__).resolve().parents[1] / "data/crops.csv"
    with path.open(encoding="utf-8", newline="") as file:
        return [{key: value if key == "crop" else float(value) for key, value in row.items()}
                for row in csv.DictReader(file)]


def solve_water(water_budget=180000, soft_orders=False, integer=False):
    crops = load_crops()
    model = pl.LpProblem("synthetic_irrigation", pl.LpMaximize)
    x = {r["crop"]: pl.LpVariable(r["crop"], 0, r["max_ha"],
                                 cat="Integer" if integer else "Continuous") for r in crops}
    profit = pl.lpSum(r["profit_brl_ha"] * x[r["crop"]] for r in crops)
    water = pl.lpSum(r["water_m3_ha"] * x[r["crop"]] for r in crops)
    capital = pl.lpSum(r["capital_brl_ha"] * x[r["crop"]] for r in crops)
    model += pl.lpSum(x.values()) <= 100, "land_ha"
    model += water <= water_budget, "physical_water_m3"
    model += capital <= 250000, "capital_brl"
    slack = {}
    for r in crops:
        key = r["crop"]
        if soft_orders:
            slack[key] = pl.LpVariable("unmet_order_" + key, 0, r["minimum_ha"])
        model += x[key] + slack.get(key, 0) >= r["minimum_ha"], "order_" + key
    if soft_orders:
        # Lexicographic rule relaxation: minimize unmet orders, then maximize profit.
        model.sense = pl.LpMinimize
        model.setObjective(pl.lpSum(slack.values()))
        model.solve(pl.PULP_CBC_CMD(msg=False))
        if model.status != pl.LpStatusOptimal:
            return dict(status=pl.LpStatus[model.status], feasible=False)
        minimum_shortfall = pl.value(model.objective)
        model += pl.lpSum(slack.values()) <= minimum_shortfall + 1e-7
        model.sense = pl.LpMaximize
    model.setObjective(profit)
    model.solve(pl.PULP_CBC_CMD(msg=False))
    if model.status != pl.LpStatusOptimal:
        return dict(status=pl.LpStatus[model.status], feasible=False,
                    minimum_water_for_orders=sum(r["minimum_ha"] * r["water_m3_ha"] for r in crops))
    areas = {key: var.value() for key, var in x.items()}
    # Recompute every physical constraint, independently of solver expressions.
    consumed = sum(r["water_m3_ha"] * areas[r["crop"]] for r in crops)
    spent = sum(r["capital_brl_ha"] * areas[r["crop"]] for r in crops)
    shortfalls = {r["crop"]: max(0, r["minimum_ha"] - areas[r["crop"]]) for r in crops}
    feasible = (sum(areas.values()) <= 100 + 1e-5 and consumed <= water_budget + 1e-4
                and spent <= 250000 + 1e-4
                and all(-1e-6 <= areas[r["crop"]] <= r["max_ha"] + 1e-6 for r in crops)
                and (soft_orders or max(shortfalls.values()) <= 1e-6)
                and (not integer or all(abs(a - round(a)) < 1e-6 for a in areas.values())))
    return dict(status="Optimal", feasible=feasible, areas_ha=areas, water_m3=consumed,
                water_budget_m3=water_budget, capital_brl=spent,
                profit_brl=sum(r["profit_brl_ha"] * areas[r["crop"]] for r in crops),
                unmet_orders_ha=shortfalls, rules_relaxed=soft_orders,
                variable_type="Integer" if integer else "Continuous")
