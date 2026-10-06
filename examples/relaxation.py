"""Compare a small integer knapsack model with its LP relaxation."""
import pulp as pl


def build_model(integer: bool):
    model = pl.LpProblem("knapsack_demo", pl.LpMaximize)
    category = pl.LpInteger if integer else pl.LpContinuous
    x = pl.LpVariable("x", lowBound=0, cat=category)
    y = pl.LpVariable("y", lowBound=0, cat=category)
    model += 3 * x + 4 * y
    model += 5 * x + 8 * y <= 24, "capacity"
    return model, x, y


for label, integer in (("LP relaxation", False), ("Integer model", True)):
    model, x, y = build_model(integer)
    status = model.solve(pl.PULP_CBC_CMD(msg=False))
    print(f"{label}: {pl.LpStatus[status]}")
    if pl.LpStatus[status] == "Optimal":
        print(f"  x={x.value():.2f}, y={y.value():.2f}, objective={pl.value(model.objective):.2f}")
        if not integer:
            rounded_x, rounded_y = round(x.value()), round(y.value())
            capacity = 5 * rounded_x + 8 * rounded_y
            print(f"  rounded x={rounded_x}, y={rounded_y}; capacity={capacity}/24")
            print("  Rounding is only a candidate; re-check every constraint.")
