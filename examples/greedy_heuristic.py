"""Greedy construction for a synthetic integer menu; no optimality proof.

For this tiny example, the score adds remaining protein and carbohydrate grams
with equal weight. Real applications need a justified scale or separate priorities.
"""
from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]
with (ROOT / "data" / "foods.csv").open(encoding="utf-8", newline="") as f:
    foods = list(csv.DictReader(f))

targets = {"protein": 60.0, "carbs": 150.0}
solution = {r["food"]: 0 for r in foods}  # number of packages
max_packages = {r["food"]: int(float(r["max_g"]) // float(r["package_g"])) for r in foods}


def totals():
    protein = carbs = cost = 0.0
    for row in foods:
        count = solution[row["food"]]
        factor = count * float(row["package_g"]) / 100
        protein += factor * float(row["protein_g_per_100g"])
        carbs += factor * float(row["carbs_g_per_100g"])
        cost += factor * float(row["cost_per_100g"])
    return protein, carbs, cost


for _ in range(sum(max_packages.values())):
    protein, carbs, _ = totals()
    p_need = max(0.0, targets["protein"] - protein)
    c_need = max(0.0, targets["carbs"] - carbs)
    if p_need <= 1e-9 and c_need <= 1e-9:
        break
    candidates = []
    for row in foods:
        food = row["food"]
        if solution[food] >= max_packages[food]:
            continue
        factor = float(row["package_g"]) / 100
        p = factor * float(row["protein_g_per_100g"])
        c = factor * float(row["carbs_g_per_100g"])
        benefit = min(p, p_need) + min(c, c_need)
        if benefit > 0:
            cost = factor * float(row["cost_per_100g"])
            candidates.append((cost / benefit, food))
    if not candidates:
        break
    _, chosen = min(candidates)
    solution[chosen] += 1

protein, carbs, cost = totals()
valid = protein >= targets["protein"] and carbs >= targets["carbs"]
print(f"Feasible: {valid}")
print(f"Protein: {protein:.1f}/{targets['protein']:.1f} g; carbs: {carbs:.1f}/{targets['carbs']:.1f} g")
print(f"Synthetic cost: ${cost:.2f}")
for food, count in solution.items():
    if count:
        print(f"{food:>8}: {count} packages")
print("This greedy result has no proof of optimality.")
