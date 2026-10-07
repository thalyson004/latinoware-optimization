"""Nearest neighbor plus 2-opt; recheck the candidate under slower traffic."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from optimization_examples.routing import load_instance, heuristic_route, evaluate_route

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--students', type=int, default=15)
    p.add_argument('--windows', action='store_true')
    p.add_argument('--time-limit', type=float, default=5)
    p.add_argument('--traffic-factor', type=float, default=1.8)
    a = p.parse_args()
    instance = load_instance(a.students, a.windows)
    candidate = heuristic_route(instance, a.time_limit)
    print(json.dumps(dict(candidate=candidate, traffic_scenario=evaluate_route(
        instance, candidate['route'], a.traffic_factor)), indent=2))
