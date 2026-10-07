"""Synthetic menus with four objectives and mandatory procurement constraint."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from optimization_examples.school import solve_milp, solve_nsga2, reference_front, audit

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--method', choices=['milp', 'nsga2', 'enumerate'], default='milp')
    p.add_argument('--seed', type=int, default=2026)
    p.add_argument('--generations', type=int, default=80)
    a = p.parse_args()
    if a.method == 'milp':
        result = solve_milp()
    else:
        if a.method == 'enumerate':
            x, _, info = reference_front()
        else:
            x, _ = solve_nsga2(a.seed, a.generations)
            info = dict(seed=a.seed, generations=a.generations, approximate=True)
        result = dict(info, menus=[audit(row) for row in x])
    print(json.dumps(result, indent=2, ensure_ascii=False))
