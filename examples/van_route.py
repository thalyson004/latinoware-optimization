"""Exact open TSP or its LP relaxation, with independently checked arrivals."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from optimization_examples.routing import load_instance, solve_route

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--students', type=int, default=5)
    p.add_argument('--windows', action='store_true')
    p.add_argument('--impossible', action='store_true')
    p.add_argument('--relax', action='store_true')
    p.add_argument('--time-limit', type=float, default=5)
    a = p.parse_args()
    print(json.dumps(solve_route(load_instance(a.students, a.windows or a.impossible, a.impossible),
                                a.time_limit, a.relax), indent=2))
