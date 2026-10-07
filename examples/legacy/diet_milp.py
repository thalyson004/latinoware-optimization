"""Package-size and food-variety MILP, using synthetic teaching data."""
from pathlib import Path
import csv

import pulp as pl

ROOT = Path(__file__).resolve().parents[2]
with (ROOT / "data" / "foods.csv").open(encoding="utf-8", newline="") as f:
    foods = list(csv.DictReader(f))

model = pl.LpProblem("illustrative_diet_packages", pl.LpMinimize)
packages = {r["food"]: pl.LpVariable(f"packages_{r['food']}", lowBound=0, cat=pl.LpInteger) for r in foods}
selected = {r["food"]: pl.LpVariable(f"selected_{r['food']}", cat=pl.LpBinary) for r in foods}
grams = {r["food"]: float(r["package_g"]) * packages[r["food"]] for r in foods}
model += pl.lpSum(float(r["cost_per_100g"]) / 100 * grams[r["food"]] for r in foods)
for r in foods:
    food = r["food"]
    model += grams[food] <= float(r["max_g"]) * selected[food], f"link_{food}"
model += pl.lpSum(selected.values()) <= 3, "variety_limit"
model += pl.lpSum(float(r["protein_g_per_100g"]) / 100 * grams[r["food"]] for r in foods) >= 60, "protein_min"
model += pl.lpSum(float(r["carbs_g_per_100g"]) / 100 * grams[r["food"]] for r in foods) >= 150, "carbs_min"
model += pl.lpSum(float(r["carbon_kg_per_100g"]) / 100 * grams[r["food"]] for r in foods) <= 2.0, "carbon_cap"
status = model.solve(pl.PULP_CBC_CMD(msg=False, timeLimit=10))
print(f"Status: {pl.LpStatus[status]}")
if pl.LpStatus[status] == "Optimal":
    print(f"Synthetic daily cost: ${pl.value(model.objective):.2f}")
    carbon = sum(float(r["carbon_kg_per_100g"]) / 100 * (pl.value(grams[r["food"]]) or 0) for r in foods)
    print(f"Illustrative emissions: {carbon:.2f} / 2.00 kg CO2e")
    for food, qty in grams.items():
        if (pl.value(qty) or 0) > 1e-6:
            print(f"{food:>8}: {pl.value(qty):7.1f} g ({pl.value(packages[food]):.0f} packages)")
