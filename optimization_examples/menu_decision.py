"""Finite, fully enumerable synthetic menus for Pareto and preference examples.

No nutrient tables, dietary advice or regulatory compliance is represented.
Adequacy is a didactic score: fraction of three invented minimum targets met.
Ultra-processed share uses invented energy units as denominator (not mass).
"""
import itertools
import numpy as np

CATEGORIES = [
 [('arroz', 1.1, [2,8,1], 100, 0), ('macarrao instantaneo', .8, [1,9,0], 110, 110), ('arroz integral', 1.8, [3,7,3], 100, 0)],
 [('feijao', 1.0, [5,4,5], 100, 0), ('lentilha', 1.5, [6,3,6], 100, 0), ('embutido', .8, [4,0,0], 120, 120)],
 [('ovo', 1.2, [7,1,0], 90, 0), ('frango', 2.5, [10,0,0], 100, 0), ('nuggets', 1.4, [6,4,0], 140, 140)],
 [('banana', .7, [1,5,2], 80, 0), ('verduras', 1.6, [2,1,5], 40, 0), ('sobremesa pronta', .5, [0,7,0], 140, 140)],
]
TARGET = np.array([18, 18, 13])  # three fictional educational indicators


def all_menus():
    rows = []
    for choice in itertools.product(range(3), repeat=4):
        foods = [CATEGORIES[j][i] for j, i in enumerate(choice)]
        total = np.sum([f[2] for f in foods], axis=0)
        adequacy = 100*float(np.mean(total >= TARGET))
        cost = round(sum(f[1] for f in foods), 2)
        up = 100*sum(f[4] for f in foods)/sum(f[3] for f in foods)
        rows.append(dict(choice=list(choice), foods=[f[0] for f in foods], cost=cost,
                         adequacy=adequacy, ultra=round(up, 3), indicators=total.tolist(),
                         targets_met=int(np.sum(total >= TARGET))))
    return rows


def objectives(rows, dimensions=3):
    f = np.array([[r['cost'], 100-r['adequacy'], r['ultra']] for r in rows])
    return f[:, :dimensions]  # all three transformed into minimization


def nondominated(f):
    f = np.asarray(f)
    return np.array([not np.any(np.all(f <= p+1e-8, axis=1) & np.any(f < p-1e-8, axis=1)) for p in f])


def frontier(rows, dimensions=3):
    return [r for r, keep in zip(rows, nondominated(objectives(rows, dimensions))) if keep]


def choose_weighted(rows, weights=(.4, .4, .2)):
    """Normalize only the supplied alternatives; weights are declared preferences."""
    f = objectives(rows)
    low, high = f.min(axis=0), f.max(axis=0)
    span = np.where(high > low, high-low, 1)
    normalized = (f-low)/span
    weights = np.asarray(weights, dtype=float)
    if np.any(weights < 0) or not np.isclose(weights.sum(), 1):
        raise ValueError('Nonnegative weights must sum to one')
    score = normalized @ weights
    chosen = int(np.argmin(score))
    return dict(menu=rows[chosen], score=float(score[chosen]), weights=weights.tolist(),
                ideal=low.tolist(), nadir=high.tolist(), normalized=normalized.tolist(), scores=score.tolist())


def aspiration(rows, budget=6, minimum_adequacy=100):
    acceptable = [r for r in rows if r['cost'] <= budget and r['adequacy'] >= minimum_adequacy]
    return min(acceptable, key=lambda r: (r['ultra'],r['cost'])) if acceptable else None
