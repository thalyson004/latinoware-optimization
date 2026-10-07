"""Run reproducible demonstrations, verify outputs and generate the deck's figures."""
from pathlib import Path
import argparse
import csv
import hashlib
import itertools
import json
import platform
import sys
from importlib.metadata import version
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from optimization_examples.routing import load_instance, solve_route, heuristic_route, evaluate_route
from optimization_examples.water import solve_water
from optimization_examples.school import solve_milp, solve_nsga2, reference_front, audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--figures', type=Path, default=ROOT / 'results/figures')
    args = parser.parse_args()
    output = ROOT / 'results'
    output.mkdir(exist_ok=True)
    args.figures.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False})
    small = load_instance(5)
    exact5 = solve_route(small)
    brute = min(evaluate_route(small, ['garagem', *p, 'IFCE'])['km']
                for p in itertools.permutations(small['students']))
    assert exact5['certified_optimal'] and exact5['feasible'] and abs(exact5['km'] - brute) < .0002
    relaxed = solve_route(small, relax=True)
    assert relaxed['lower_bound_km'] <= exact5['km'] + 1e-5
    normal = load_instance(15)
    windows = load_instance(15, windows=True)
    exact15 = solve_route(normal, time_limit=5)
    exact_windows = solve_route(windows, time_limit=5)
    heuristic = heuristic_route(normal)
    heuristic_windows = heuristic_route(windows)
    assert heuristic['feasible']
    impossible = solve_route(load_instance(5, windows=True, impossible=True))
    assert impossible['status'] == 'Infeasible'
    traffic = evaluate_route(windows, heuristic_windows['route'], traffic_factor=1.8)
    water = solve_water()
    drought = solve_water(40000)
    flexible = solve_water(40000, soft_orders=True)
    integer_water = solve_water(integer=True)
    assert water['feasible'] and drought['status'] == 'Infeasible' and flexible['feasible']
    assert flexible['water_m3'] <= 40000 + .001 and integer_water['feasible']
    frontier = [solve_water(b) for b in range(50000, 260001, 10000)]
    menu = solve_milp()
    reference_x, reference_f, reference_info = reference_front()
    nsga_x, nsga_f = solve_nsga2()
    assert menu['feasible'] and abs(menu['cost_brl'] - reference_info['minimum_cost']) < 1e-6
    assert len(nsga_x) and all(audit(x)['feasible'] for x in nsga_x)
    dominated = sum(bool(np.any(np.all(reference_f <= f + 1e-8, axis=1)
                                & np.any(reference_f < f - 1e-8, axis=1))) for f in nsga_f)
    covered = sum(bool(np.any(np.all(np.isclose(nsga_f, f, atol=1e-8), axis=1))) for f in reference_f)
    with (output / 'menu-front.csv').open('w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['method', 'arroz', 'feijao', 'frango', 'abobora', 'banana', 'leite',
                         'cost_brl', 'nutrition_deviation', 'negative_family_spend_brl', 'carbon_kgco2e'])
        for method, xs, fs in [('enumeration', reference_x, reference_f), ('nsga2', nsga_x, nsga_f)]:
            writer.writerows([method, *map(int, x), *map(float, f)] for x, f in zip(xs, fs))
    report = dict(python=platform.python_version(), seed=2026,
        packages={k: version(k) for k in ['pulp', 'networkx', 'numpy', 'matplotlib', 'pymoo']},
        data_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'data').glob('*.csv')},
        routing=dict(exact5=exact5, brute5_km=brute, relaxed5=relaxed, exact15=exact15,
                     exact15_windows=exact_windows, heuristic15=heuristic,
                     heuristic15_windows=heuristic_windows, impossible=impossible, traffic=traffic),
        water=dict(normal=water, drought=drought, flexible=flexible, integer=integer_water, tradeoff=frontier),
        school=dict(milp=menu, reference=reference_info, nsga2=dict(seed=2026, generations=80,
                    solutions=len(nsga_x), dominated_by_grid=dominated,
                    reference_objectives_covered=covered, all_audited_feasible=True)),
        slm=dict(status='Prompt only; no local model inference performed'))
    (output/'demo-results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    fig, ax = plt.subplots(figsize=(8, 4.5), layout='constrained')
    graph = normal['graph']
    route = heuristic['route']
    pos = {p: (graph.nodes[p]['x'], graph.nodes[p]['y']) for p in graph}
    for p in route:
        px, py = pos[p]
        ax.scatter(px, py, color='#685BC7', s=45)
        label = p.replace('aluno_', '')
        ax.annotate(label, (px, py), xytext=(4, 5), textcoords='offset points', fontsize=9)
    ax.plot([pos[p][0] for p in route], [pos[p][1] for p in route], color='#685BC7', alpha=.6)
    ax.set(xlabel='Coordenada sintética (km)', ylabel='Coordenada sintética (km)',
           title='15 alunos: vizinho mais próximo + 2-opt')
    fig.savefig(args.figures/'van-route.pdf'); plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 4.2), layout='constrained')
    ax.plot([s['water_m3']/1000 for s in frontier], [s['profit_brl']/1000 for s in frontier],
            'o-', color='#685BC7')
    ax.set(xlabel='Água utilizada (mil m³)', ylabel='Lucro sintético (mil R$)',
           title='Resolver o LP para diferentes cotas de água')
    fig.savefig(args.figures/'water-tradeoff.pdf'); plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 4.2), layout='constrained')
    ax.scatter(reference_f[:,0], reference_f[:,3], color='#cfc9ec', s=28, label='Referência da grade')
    points = ax.scatter(nsga_f[:,0], nsga_f[:,3], c=-nsga_f[:,2], cmap='viridis', s=32, label='NSGA-II')
    fig.colorbar(points, ax=ax, label='Compra familiar (R$)')
    ax.set(xlabel='Custo de 100 refeições (R$)', ylabel='Emissões sintéticas (kg CO₂e)',
           title='Projeção de uma fronteira com quatro objetivos')
    ax.legend(fontsize=9)
    fig.savefig(args.figures/'menu-pareto.pdf'); plt.close(fig)
    print(json.dumps(dict(exact5_km=exact5['km'], exact15_status=exact15['status'],
                         windows_status=exact_windows['status'], heuristic_km=heuristic['km'],
                         school=report['school']), indent=2))


if __name__ == '__main__':
    main()
