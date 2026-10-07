"""Synthetic representative menu; procurement accounts for 100 meals, not a real network."""
from pathlib import Path
import csv
import itertools
import numpy as np
import pulp as pl

NAMES = ['energy_kcal', 'protein_g', 'fiber_g', 'calcium_mg']
LOW = np.array([450, 18, 5, 150])
HIGH = np.array([650, 40, 20, 600])
TARGET = np.array([550, 28, 10, 200])
MEALS, FNDE_BUDGET = 100, 600


def data():
    with (Path(__file__).resolve().parents[1] / 'data/school_foods.csv').open(encoding='utf-8') as file:
        rows = list(csv.DictReader(file))
    nutrients = np.array([[float(r[k]) for k in NAMES] for r in rows])
    cost = np.array([float(r['cost_brl_portion']) for r in rows]) * MEALS
    carbon = np.array([float(r['carbon_kgco2e']) for r in rows]) * MEALS
    family = cost * np.array([int(r['family_supplier']) for r in rows])
    return rows, nutrients, cost, carbon, family


def evaluate(x):
    x = np.atleast_2d(x)
    _, nutrients, cost, carbon, family = data()
    n = x @ nutrients
    f = np.column_stack([x @ cost, np.mean(abs(n - TARGET) / TARGET, axis=1),
                         -(x @ family), x @ carbon])
    g = np.column_stack([LOW - n, n - HIGH, x @ cost - FNDE_BUDGET,
                         .45 * FNDE_BUDGET - x @ family, x.sum(axis=1) - 14,
                         3 - (x > 0).sum(axis=1)])
    return f, g


def audit(x):
    x = np.asarray(x, dtype=float)
    f, g = evaluate(x)
    rows, nutrients, *_ = data()
    return dict(feasible=bool(np.max(g) <= 1e-6 and np.all(x >= 0) and np.all(x <= 4)
                              and np.max(abs(x - np.round(x))) <= 1e-6),
                portions={r['food']: int(round(v)) for r, v in zip(rows, x)},
                cost_brl=float(f[0, 0]), nutrition_deviation=float(f[0, 1]),
                family_spend_brl=float(-f[0, 2]), carbon_kgco2e=float(f[0, 3]),
                family_fraction_fnde=float(-f[0, 2] / FNDE_BUDGET),
                nutrients=dict(zip(NAMES, map(float, x @ nutrients))))


def solve_milp():
    rows, nutrients, cost, _, family = data()
    model = pl.LpProblem('synthetic_school_menu', pl.LpMinimize)
    x = [pl.LpVariable(r['food'], 0, 4, cat='Integer') for r in rows]
    y = [pl.LpVariable('selected_' + r['food'], cat='Binary') for r in rows]
    model += pl.lpDot(cost, x)
    model += pl.lpDot(cost, x) <= FNDE_BUDGET
    model += pl.lpDot(family, x) >= .45 * FNDE_BUDGET
    model += pl.lpSum(x) <= 14
    model += pl.lpSum(y) >= 3
    for a, b in zip(x, y):
        model += a <= 4 * b
        model += a >= b
    for k in range(4):
        model += pl.lpDot(nutrients[:, k], x) >= LOW[k]
        model += pl.lpDot(nutrients[:, k], x) <= HIGH[k]
    model.solve(pl.PULP_CBC_CMD(msg=False))
    if model.status != pl.LpStatusOptimal:
        return dict(status=pl.LpStatus[model.status], feasible=False)
    return dict(audit([v.value() for v in x]), status='Optimal', certified_optimal=True)


def reference_front():
    from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting
    x = np.array(list(itertools.product(range(5), repeat=6)))
    f, g = evaluate(x)
    valid = np.all(g <= 1e-6, axis=1)
    x, f = x[valid], f[valid]
    indices = NonDominatedSorting().do(f, only_non_dominated_front=True)
    return x[indices], f[indices], dict(enumerated=5**6, feasible=int(valid.sum()),
                                     nondominated=len(indices), minimum_cost=float(f[:, 0].min()))


def solve_nsga2(seed=2026, generations=80):
    from pymoo.core.problem import Problem
    from pymoo.algorithms.moo.nsga2 import NSGA2
    from pymoo.operators.sampling.rnd import IntegerRandomSampling
    from pymoo.operators.crossover.sbx import SBX
    from pymoo.operators.mutation.pm import PM
    from pymoo.operators.repair.rounding import RoundingRepair
    from pymoo.optimize import minimize
    class MenuProblem(Problem):
        def __init__(self):
            super().__init__(n_var=6, n_obj=4, n_ieq_constr=12, xl=0, xu=4, vtype=int)
        def _evaluate(self, x, out, *args, **kwargs):
            out['F'], out['G'] = evaluate(x)
    algorithm = NSGA2(pop_size=120, sampling=IntegerRandomSampling(),
                      crossover=SBX(prob=.9, eta=15, vtype=float, repair=RoundingRepair()),
                      mutation=PM(eta=20, vtype=float, repair=RoundingRepair()), eliminate_duplicates=True)
    result = minimize(MenuProblem(), algorithm, ('n_gen', generations), seed=seed, verbose=False)
    if result.X is None:
        return np.empty((0, 6), dtype=int), np.empty((0, 4))
    return np.atleast_2d(result.X).astype(int), np.atleast_2d(result.F)
