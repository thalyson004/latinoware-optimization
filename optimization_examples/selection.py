"""Synthetic multidimensional knapsack: which indivisible kits go in the van?

Benefit scores are invented priorities, not measured social/nutritional impact.
The large instance is a computational stress example, not a real delivery plan.
"""
from pathlib import Path
import itertools
import re
import time
import numpy as np
import pulp as pl


def small_instance():
    return dict(names=['Arroz', 'Feijao', 'Frutas', 'Leite', 'Legumes', 'Ovos'],
                value=np.array([12, 10, 9, 8, 11, 7], dtype=float),
                use=np.array([[6, 5, 4, 3, 5, 2], [4, 3, 5, 2, 4, 2]], dtype=float),
                capacity=np.array([15, 12], dtype=float),
                resources=['peso_kg', 'volume_unidades'], seed=None)


def stress_instance(seed=2026, n=250, resources=10):
    rng = np.random.default_rng(seed)
    use = rng.integers(1, 100, (resources, n)).astype(float)
    return dict(names=[f'kit_{i:03}' for i in range(n)],
                value=rng.integers(10, 100, n).astype(float), use=use,
                capacity=np.floor(.25 * use.sum(axis=1)),
                resources=[f'recurso_{j}' for j in range(resources)], seed=seed)


def audit(instance, x, integer=True):
    x = np.asarray(x, dtype=float)
    valid = bool(x.shape == instance['value'].shape and np.all(np.isfinite(x)))
    if not valid:
        return dict(feasible=False)
    used = instance['use'] @ x
    feasible = bool(np.all(x >= -1e-6) and np.all(x <= 1+1e-6)
                    and np.all(used <= instance['capacity']+1e-5)
                    and (not integer or np.all(np.abs(x-np.rint(x)) < 1e-5)))
    return dict(feasible=feasible, objective=float(instance['value'] @ x),
                used=used.tolist(), capacity=instance['capacity'].tolist())


def build_model(instance, relax=False):
    model = pl.LpProblem('kits_na_van', pl.LpMaximize)
    x = [pl.LpVariable(f'x_{i}', 0, 1, cat='Continuous' if relax else 'Binary')
         for i in range(len(instance['value']))]
    model += pl.lpSum(float(v)*z for v, z in zip(instance['value'], x))
    for j, capacity in enumerate(instance['capacity']):
        model += pl.lpSum(float(a)*z for a, z in zip(instance['use'][j], x)) <= float(capacity)
    return model, x


def solve(instance, relax=False, time_limit=5, log_path=None):
    model, x = build_model(instance, relax)
    options = dict(msg=False, timeLimit=time_limit,
                   options=['randomSeed 2026', 'randomCbcSeed 2026'])
    if log_path:
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        options['logPath'] = str(log_path)
    started = time.perf_counter()
    model.solve(pl.PULP_CBC_CMD(**options))
    elapsed = time.perf_counter()-started
    values = [v.value() for v in x]
    evidence = audit(instance, values, integer=not relax) if all(v is not None for v in values) else dict(feasible=False)
    certified = bool(model.status == pl.LpStatusOptimal and model.sol_status == pl.LpSolutionOptimal
                     and evidence['feasible'])
    log = Path(log_path).read_text(errors='replace') if log_path else ''
    summary = [line for line in log.splitlines() if re.search(
        r'Result -|Objective value:|Upper bound:|Gap:|Time \(Wallclock|Stopped on time', line)]
    status = ('LP ótimo' if relax else 'Ótimo certificado') if certified else (
        'Inviável' if model.status == pl.LpStatusInfeasible else
        'Viável; ótimo não certificado' if evidence['feasible'] else 'Sem solução viável encontrada')
    return dict(status=status, solver_status=pl.LpStatus[model.status],
                solution_status=pl.LpSolution[model.sol_status], certified=certified,
                feasible=evidence['feasible'], objective=evidence.get('objective') if evidence['feasible'] else None,
                x=values if evidence['feasible'] else None, seconds=round(elapsed, 4),
                time_limit=time_limit, fractional_variables=sum(abs(v-round(v)) > 1e-5 for v in values if v is not None),
                log_summary=summary, audit=evidence)


def enumerate_small(instance):
    feasible = []
    for x in itertools.product([0, 1], repeat=len(instance['value'])):
        evidence = audit(instance, x)
        if evidence['feasible']:
            feasible.append((evidence['objective'], list(x)))
    value, x = max(feasible)
    return dict(objective=value, x=x, configurations=2**len(instance['value']), feasible_count=len(feasible))


def repair(instance, x, rng=None):
    """Keep feasible selected kits, then fill free capacity; never exceed resources."""
    score = instance['value'] / (instance['use']/instance['capacity'][:, None]).sum(axis=0)
    if rng is not None:
        score = score * rng.uniform(.65, 1.35, len(score))
    order = np.argsort(-score)
    selected = np.zeros(len(x), dtype=int)
    remaining = instance['capacity'].copy()
    for candidates in (order[np.asarray(x)[order] > .5], order):
        for i in candidates:
            if not selected[i] and np.all(instance['use'][:, i] <= remaining+1e-8):
                selected[i] = 1
                remaining -= instance['use'][:, i]
    return selected


def greedy(instance):
    x = repair(instance, np.zeros(len(instance['value'])))
    return dict(x=x.tolist(), **audit(instance, x))


def genetic(instance, seed=2026, population=50, generations=30):
    rng = np.random.default_rng(seed)
    n = len(instance['value'])
    started = time.perf_counter()
    pop = np.array([repair(instance, rng.integers(0, 2, n), rng) for _ in range(population)])
    pop[0] = greedy(instance)['x']
    history = []
    for generation in range(generations+1):
        values = pop @ instance['value']
        best = int(np.argmax(values))
        history.append(float(values[best]))
        if generation == generations:
            break
        new = [pop[best].copy()]  # elitism: keep the best feasible candidate
        while len(new) < population:
            parents = []
            for _ in range(2):
                contenders = rng.integers(0, population, 3)
                parents.append(pop[contenders[np.argmax(values[contenders])]])
            child = np.where(rng.random(n) < .5, parents[0], parents[1])
            flip = rng.random(n) < 1/n
            child[flip] = 1-child[flip]
            new.append(repair(instance, child, rng))
        pop = np.array(new)
    x = pop[best]
    return dict(x=x.tolist(), **audit(instance, x), seconds=round(time.perf_counter()-started, 4),
                seed=seed, population=population, generations=generations, history=history,
                certified=False, evaluations=population*(generations+1))
