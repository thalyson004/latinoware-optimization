"""Prepare a modeling prompt or request an Ollama draft; never execute generated code."""
import argparse
import json
import urllib.request
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from optimization_examples.water import load_crops

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--model', help='Name of an already installed local Ollama model')
    a = p.parse_args()
    prompt = ('Formule em português um LP de hectares contínuos. Dados sintéticos: ' +
              json.dumps(load_crops(), ensure_ascii=False) +
              '. Terra: 100 ha; água: 180000 m³; capital: R$250000. Maximize lucro. '
              'Respeite máximos e mínimos por cultura. Retorne variáveis, unidades, objetivo, '
              'restrições e hipóteses. Não acrescente números. Não gere código executável.')
    payload = dict(model=a.model, messages=[dict(role='user', content=prompt)], stream=False,
                   options=dict(temperature=0))
    if a.dry_run:
        print(json.dumps(dict(status='Prompt only; no inference performed', request=payload),
                         ensure_ascii=False, indent=2))
    elif not a.model:
        p.error('Use --dry-run or specify --model for local inference.')
    else:
        request = urllib.request.Request('http://localhost:11434/api/chat',
            data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(request, timeout=180) as response:
            result = json.load(response)
        print(json.dumps(dict(status='Unvalidated modeling draft', response=result),
                         ensure_ascii=False, indent=2))
