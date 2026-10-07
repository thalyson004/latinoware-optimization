"""Synthetic crop planning: drought, rule relaxation or integer hectare blocks."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from optimization_examples.water import solve_water

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--water-budget', type=float, default=180000)
    p.add_argument('--soft-orders', action='store_true')
    p.add_argument('--integer', action='store_true')
    a = p.parse_args()
    print(json.dumps(solve_water(a.water_budget, a.soft_orders, a.integer), indent=2))
