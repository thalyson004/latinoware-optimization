"""Tiny continuous diet LP; every coefficient is synthetic and educational."""
from pathlib import Path
import csv

import pulp as pl

ROOT = Path(__file__).resolve().parents[2]
with (ROOT / "data" / "foods.csv").open(encoding="utf-8", newline="") as f:
    foods = list(csv.DictReader(f))

model = pl.LpProblem("illustrative_diet", pl.LpMinimize)
x = {r["food"]: pl.LpVariable(f"grams_{r['food']}", lowBound=0, upBound=float(r["max_g"])) for r in foods}
model += pl.lpSum(float(r["cost_per_100g"]) / 100 * x[r["food"]] for r in foods), "daily_cost"
model += pl.lpSum(float(r["protein_g_per_100g"]) / 100 * x[r["food"]] for r in foods) >= 60, "protein_min"
model += pl.lpSum(float(r["carbs_g_per_100g"]) / 100 * x[r["food"]] for r in foods) >= 150, "carbs_min"
# Illustrative emissions cap; all values in foods.csv are synthetic too.
model += pl.lpSum(float(r["carbon_kg_per_100g"]) / 100 * x[r["food"]] for r in foods) <= 1.30, "carbon_cap"
status = model.solve(pl.PULP_CBC_CMD(msg=False))
print(f"Status: {pl.LpStatus[status]}")
if pl.LpStatus[status] == "Optimal":
    print(f"Synthetic daily cost: ${pl.value(model.objective):.2f}")
    carbon = sum(float(r["carbon_kg_per_100g"]) / 100 * (x[r["food"]].value() or 0) for r in foods)
    print(f"Illustrative emissions: {carbon:.2f} / 1.30 kg CO2e")
    for food, var in x.items():
        if (var.value() or 0) > 1e-6:
            print(f"{food:>8}: {var.value():7.1f} g")
