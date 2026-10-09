"""Export measured notebook results and figures; never invent demonstration values."""
from pathlib import Path
import argparse
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--presentation',type=Path,default=ROOT.parent/'presentation')
    args = parser.parse_args()
    source = ROOT/'results/sequence'
    output = args.presentation/'figs/sequence'
    output.mkdir(parents=True,exist_ok=True)
    for name in ['ga-history.pdf','pareto-2d.pdf','pareto-3d.pdf']:
        shutil.copy2(source/name,output/name)
    load = lambda name: json.loads((source/(name+'.json')).read_text(encoding='utf-8'))
    small, stress, lp, ga, decision = [load(n) for n in ['small','stress','relaxation','genetic','decision']]
    if stress['certified'] or not stress['feasible'] or not any('Stopped on time limit' in line for line in stress['log_summary']):
        raise ValueError('O caso de estresse encerrou de outra forma. Revise sua interpretação nos slides antes de exportar.')
    if not small['certified'] or not all(r['certified'] for r in lp.values()):
        raise ValueError('A narrativa pressupõe ótimo pequeno e limites LP certificados; conferir a execução.')
    def num(value,places=2):
        return f'{value:.{places}f}'.replace('.',',')
    values = dict(SmallValue=num(small['objective'],0), SmallSeconds=num(small['seconds'],4),
                  SmallSelection=' + '.join(n for n,x in zip(['Arroz','Feijão','Frutas','Leite','Legumes','Ovos'],small['x']) if x>.5),
                  StressValue=num(stress['objective'],0) if stress['objective'] is not None else '---',
                  StressSeconds=num(stress['seconds'],4), SmallLP=num(lp['small']['objective'],3),
                  StressLP=num(lp['stress']['objective'],3), GreedyValue=num(ga['greedy']['objective'],0),
                  GAValue=num(ga['ga']['objective'],0), GASeconds=num(ga['ga']['seconds'],4),
                  FrontTwo=str(len(decision['front2'])),FrontThree=str(len(decision['front3'])),
                  CostChoice=num(decision['cost_priority']['menu']['cost']),
                  CostAdequacy=num(decision['cost_priority']['menu']['adequacy'],1),
                  CostUltra=num(decision['cost_priority']['menu']['ultra'],1),
                  HealthChoice=num(decision['health_priority']['menu']['cost']),
                  HealthAdequacy=num(decision['health_priority']['menu']['adequacy'],1),
                  HealthUltra=num(decision['health_priority']['menu']['ultra'],1),
                  AspirationCost=num(decision['aspiration']['cost']),
                  AspirationUltra=num(decision['aspiration']['ultra'],1))
    # Derive the upper bound from the actual CBC log; LP bound remains separate.
    for line in stress['log_summary']:
        if 'Upper bound:' in line:
            values['StressCBCBound']=num(float(line.split(':')[1]),3)
    values.setdefault('StressCBCBound','---')
    tex = ['% Generated from executed notebooks; synthetic data, one run.']
    tex += ['\\newcommand{\\'+key+'}{'+value+'}' for key,value in values.items()]
    (output/'results.tex').write_text('\n'.join(tex)+'\n',encoding='utf-8')
    loglines = stress['log_summary']
    (output/'stress-log.txt').write_text('\n'.join(loglines)+'\n',encoding='utf-8')
    print('Figures, result macros and actual solver summary exported.')


if __name__ == '__main__':
    main()
