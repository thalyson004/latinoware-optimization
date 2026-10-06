"""Show hard infeasibility and explicit, penalized shortfall variables."""
import pulp as pl

# Synthetic one-food illustration: 100 g chicken costs $0.90, has 27 g protein.
hard = pl.LpProblem("impossible_budget", pl.LpMinimize)
grams = pl.LpVariable("chicken_g", lowBound=0, upBound=100)
hard += 0.009 * grams
hard += 0.27 * grams >= 60, "protein_min"
hard += 0.009 * grams <= 0.50, "budget_max"
hard_status = hard.solve(pl.PULP_CBC_CMD(msg=False))
print(f"Hard model status: {pl.LpStatus[hard_status]}")

# Relax only the protein target. The printed shortfall is visible and priced.
# This penalty weight is arbitrary teaching data, not an economic valuation.
soft = pl.LpProblem("protein_shortfall", pl.LpMinimize)
grams_soft = pl.LpVariable("chicken_g", lowBound=0, upBound=100)
shortfall = pl.LpVariable("protein_shortfall_g", lowBound=0)
soft += 0.009 * grams_soft + 0.05 * shortfall
soft += 0.27 * grams_soft + shortfall >= 60, "protein_with_shortfall"
soft += 0.009 * grams_soft <= 0.50, "budget_max"
soft_status = soft.solve(pl.PULP_CBC_CMD(msg=False))
print(f"Soft model status: {pl.LpStatus[soft_status]}")
if pl.LpStatus[soft_status] == "Optimal":
    print(f"Chicken: {grams_soft.value():.1f} g; unmet protein target: {shortfall.value():.1f} g")
