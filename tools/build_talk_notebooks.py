"""Create and execute six notebooks; publish their actual outputs for the slides.

Run with the project virtual environment, from any directory. No test suite is
invoked: these are the demonstrations requested for the talk.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import platform
import sys
import tempfile
from importlib.metadata import version
import nbformat as nb
from nbclient import NotebookClient
from jupyter_client.kernelspec import KernelSpecManager

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding='utf-8')

SETUP = """from pathlib import Path
import sys, json, numpy as np
ROOT = Path.cwd().resolve()
if not (ROOT / 'optimization_examples').is_dir():
    ROOT = ROOT.parent  # notebooks opened from codes/notebooks/
if not (ROOT / 'optimization_examples').is_dir():
    raise RuntimeError('Abra o notebook a partir do repositório codes ou codes/notebooks.')
sys.path.insert(0, str(ROOT))
OUT = ROOT / 'results' / 'sequence'
OUT.mkdir(parents=True, exist_ok=True)
def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
"""


def notebook(title, cells):
    value = nb.v4.new_notebook()
    value.cells = [nb.v4.new_markdown_cell(title), nb.v4.new_code_cell(SETUP)]
    for kind, content in cells:
        value.cells.append(nb.v4.new_markdown_cell(content) if kind == 'md' else nb.v4.new_code_cell(content))
    value.metadata.kernelspec = dict(name='latinoware-local', display_name='Latinoware Python', language='python')
    value.metadata.language_info = dict(name='python',version=platform.python_version())
    return value


NOTEBOOKS = [
('01_problemas.ipynb', '# 1. Problemas e crescimento das combinações', [
('md', 'Uma regra if/else seleciona uma ação. Dijkstra resolve exatamente o menor caminho com pesos não negativos. Nem todo problema combinatório é NP-difícil.'),
('code', """import networkx as nx
grafo = nx.Graph()
grafo.add_weighted_edges_from([('Casa','A',2),('A','Escola',3),('Casa','B',1),('B','Escola',7)])
print('Regra:', 'sair agora' if 18 < 19 else 'aula iniciou')
print('Menor caminho:', nx.shortest_path(grafo, 'Casa', 'Escola', weight='weight'))
print('Distância:', nx.shortest_path_length(grafo, 'Casa', 'Escola', weight='weight'))"""),
('md', 'Com garagem e destino fixos, a ordem de n visitas tem n! possibilidades. A tabela abaixo SUPÕE 1 milhão de rotas completas avaliadas por segundo: não é benchmark de solver. P versus NP permanece aberto.'),
('code', """import math
tabela = []
for n in [5, 10, 15, 20, 25]:
    count = math.factorial(n)
    seconds = count/1_000_000
    tabela.append(dict(visitas=n, rotas=count, segundos=seconds, anos=seconds/(365.25*86400)))
    print(n, f'{count:,} rotas', f'{seconds:.3g} s', f'{seconds/(365.25*86400):.3g} anos')
save('complexity.json', tabela)"""),
]),
('02_formulacao.ipynb', '# 2. Formular: quais kits vão na van?', [
('md', 'Dados inteiramente sintéticos. Cada kit é indivisível, disponível uma vez. A prioridade é um escore inventado; não representa benefício social medido. A van admite 15 kg e 12 unidades de volume. Maximize a prioridade respeitando ambos.'),
('code', """from optimization_examples.selection import small_instance, build_model, enumerate_small
instance = small_instance()
for i, nome in enumerate(instance['names']):
    print(nome, 'prioridade', instance['value'][i], 'peso/volume', instance['use'][:,i].tolist())"""),
('md', r'Variáveis: $x_i\in\{0,1\}$. Objetivo: $\max\sum_i v_ix_i$. Regras: $\sum_i a_{ji}x_i\le b_j$ para peso e volume. É programação linear inteira binária (não LP contínua).'),
('code', """model, variables = build_model(instance)
print(model)
reference = enumerate_small(instance)
print('Enumeração completa:', reference)
save('enumeration.json', reference)"""),
]),
('03_solver_e_limites.ipynb', '# 3. Resolver e reconhecer o limite do solver', [
('md', 'PuLP é a interface de modelagem; CBC é o solver aberto. O exemplo usa PuLP 3.3.x. Não interpretar apenas LpStatus: observar também sol_status, log e viabilidade. O limite de tempo não é prova de inviabilidade.'),
('code', """import pulp as pl
from optimization_examples.selection import small_instance, stress_instance, solve
print('PuLP:', pl.__version__, 'Solvers:', pl.listSolvers(onlyAvailable=True))
small = solve(small_instance(), log_path=OUT/'small-cbc.log')
print(small['status'], 'prioridade:', small['objective'], 'seleção:', small['x'])
save('small.json', small)"""),
('md', 'A instância de estresse tem 250 kits e dez recursos artificiais. Ela preserva o modelo, amplia seu tamanho e impõe 0,3 s ao CBC. É demonstração computacional, não descrição de uma operação real. Pode encerrar de outra forma em outra máquina.'),
('code', """large = solve(stress_instance(), time_limit=.3, log_path=OUT/'stress-cbc.log')
print('Status verificado:', large['status'])
print('Status PuLP:', large['solver_status'], '/', large['solution_status'])
print('Prioridade viável:', large['objective'], 'tempo medido:', large['seconds'])
for line in large['log_summary']: print(line)
save('stress.json', large)"""),
]),
('04_relaxamentos.ipynb', '# 4. Relaxar integridade e flexibilizar metas são operações diferentes', [
('md', 'Relaxação linear: trocar x binária por 0 ≤ x ≤ 1. Para MAXIMIZAÇÃO, o ótimo LP é um limite SUPERIOR. Uma fração de kit não é uma entrega válida. Arredondar pode perder qualidade ou violar limites.'),
('code', """from optimization_examples.selection import small_instance, stress_instance, solve, audit
small_lp = solve(small_instance(), relax=True, log_path=OUT/'small-lp.log')
large_lp = solve(stress_instance(), relax=True, log_path=OUT/'stress-lp.log')
for nome, res in [('pequena',small_lp),('estresse',large_lp)]:
    print(nome, res['status'], 'limite superior:', round(res['objective'],3), 'fracionárias:', res['fractional_variables'])
rounded = np.rint(small_lp['x'])
print('Arredondamento ao inteiro mais próximo:', rounded, audit(small_instance(), rounded))
save('relaxation.json', dict(small=small_lp, stress=large_lp))"""),
('md', 'Diagnóstico separado: se nem LP é viável, o modelo inteiro também é inviável. Se LP é viável, o inteiro ainda pode ser inviável. Não flexibilizar peso físico; só uma meta declarada negociável.'),
('code', """import pulp as pl
from optimization_examples.selection import small_instance, build_model
instance = small_instance()
hard, x = build_model(instance)
hard += pl.lpSum(v*z for v,z in zip(instance['value'],x)) >= 50, 'meta_prioridade'
hard.solve(pl.PULP_CBC_CMD(msg=False))
print('Meta >= 50 com as capacidades originais:',pl.LpStatus[hard.status])
soft, x = build_model(instance)
shortfall = pl.LpVariable('deficit_meta',lowBound=0)
soft += pl.lpSum(v*z for v,z in zip(instance['value'],x)) + shortfall >= 50
# Nova política: minimizar déficit; as capacidades permanecem obrigatórias.
soft.sense = pl.LpMinimize
soft.setObjective(shortfall)
soft.solve(pl.PULP_CBC_CMD(msg=False))
print('Meta flexibilizada:',pl.LpStatus[soft.status],'déficit:',shortfall.value())
print('É solução de OUTRO modelo, que permite déficit de prioridade.')
save('soft-target.json',dict(hard_status=pl.LpStatus[hard.status],soft_status=pl.LpStatus[soft.status],shortfall=shortfall.value()))"""),
('code', """from optimization_examples.menu_decision import all_menus
menus = all_menus()
full = [m for m in menus if m['adequacy']==100]
print('Menus possíveis:',len(menus),'que cumprem as três metas:',len(full))
print('Maior fração de metas atingidas:',max(m['adequacy'] for m in menus))
print('Flexibilizar metas muda o problema; não certifica a viabilidade do modelo original.')"""),
]),
('05_algoritmo_genetico.ipynb', '# 5. Heurística com soluções viáveis: um algoritmo genético', [
('md', 'Mesmo problema de seleção. Cromossomo: vetor binário. Fitness: prioridade total. Torneio escolhe pais, cruzamento uniforme combina bits, mutação altera escolhas e reparo mantém as capacidades. Elitismo conserva o melhor candidato. Metas negociáveis podem receber penalidades; restrições físicas continuam obrigatórias.'),
('code', """from optimization_examples.selection import stress_instance, repair, audit
instance = stress_instance()
rng = np.random.default_rng(2026)
pai = repair(instance,rng.integers(0,2,250),rng)
mae = repair(instance,rng.integers(0,2,250),rng)
filho = np.where(rng.random(250)<.5,pai,mae)  # cruzamento uniforme
mutar = rng.random(250)<1/250
filho[mutar] = 1-filho[mutar]
filho = repair(instance,filho,rng)
print('Fitness:',float(instance['value']@filho),'auditoria:',audit(instance,filho)['feasible'])"""),
('code', """from optimization_examples.selection import stress_instance, greedy, genetic
instance = stress_instance()
baseline = greedy(instance)
ga = genetic(instance, seed=2026, population=50, generations=30)
print('Gulosa:',baseline['objective'],'viável:',baseline['feasible'])
print('Genético:',ga['objective'],'viável:',ga['feasible'],'tempo:',ga['seconds'])
print('Semente/população/gerações:',ga['seed'],ga['population'],ga['generations'])
print('Nenhum certificado de ótimo. O reparo garante viabilidade neste modelo de limites superiores.')
save('genetic.json', dict(greedy=baseline, ga=ga))"""),
('code', """import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(6,3))
ax.plot(ga['history'],color='#685BC7')
ax.set(xlabel='Geração',ylabel='Melhor prioridade viável',title='Uma execução do AG; não é benchmark estatístico')
fig.tight_layout(); fig.savefig(OUT/'ga-history.pdf'); plt.show()"""),
]),
('06_pareto_e_decisao.ipynb', '# 6. Multiobjetivo: construir alternativas e escolher com critérios', [
('md', '81 cardápios: uma opção em cada uma das quatro categorias. Três indicadores nutricionais e alvos são inventados, sem unidades clínicas. Adequação = porcentagem desses três alvos atingidos; não diagnóstico de saúde. Fração ultraprocessada = energia fictícia de itens marcados / energia fictícia total. Não representa todo o PNAE.'),
('code', """from optimization_examples.menu_decision import all_menus, frontier, choose_weighted, aspiration
menus = all_menus()
front2 = frontier(menus,2)
front3 = frontier(menus,3)
print('Universo:',len(menus),'Pareto 2D:',len(front2),'Pareto 3D:',len(front3))
print('Melhor adequação:',max(m['adequacy'] for m in menus),'%')
for m in front3: print(m['foods'],'R$',m['cost'],'adequação',round(m['adequacy'],2),'%','UP',m['ultra'],'%')"""),
('md', 'Enumeração de TODOS os 81 menus permite afirmar fronteira exata somente desta grade. NSGA-II pode aproximar frentes maiores, sem garantia de encontrá-las completas. A projeção 2D da frente 3D não necessariamente é a frente ótima de dois objetivos.'),
('code', """import matplotlib.pyplot as plt
plt.rcParams.update({'font.size':14,'xtick.labelsize':12,'ytick.labelsize':12,'legend.fontsize':11})
fig,ax=plt.subplots(figsize=(6,3.5))
ax.scatter([m['cost'] for m in menus],[m['adequacy'] for m in menus],color='#D0CBDD',label='81 menus')
ax.scatter([m['cost'] for m in front2],[m['adequacy'] for m in front2],color='#685BC7',label='Pareto exato 2D')
ax.set(xlabel='Custo sintético (R$)',ylabel='Metas atingidas (%)'); ax.legend(); fig.tight_layout()
fig.savefig(OUT/'pareto-2d.pdf'); plt.show()
fig=plt.figure(figsize=(6,4)); ax=fig.add_subplot(projection='3d')
ax.scatter([m['cost'] for m in menus],[m['adequacy'] for m in menus],[m['ultra'] for m in menus],color='#CCCCCC',alpha=.3)
ax.scatter([m['cost'] for m in front3],[m['adequacy'] for m in front3],[m['ultra'] for m in front3],color='#685BC7',s=70)
ax.set(xlabel='Custo (R$)',ylabel='Adequação (%)',zlabel='UP: energia (%)'); ax.view_init(24,125)
ax.tick_params(labelsize=12)
fig.subplots_adjust(left=0,right=.90,bottom=.05,top=1); fig.savefig(OUT/'pareto-3d.pdf'); plt.show()"""),
('md', 'Decisão multicritério: declarar direção, normalizar escalas e justificar preferências. Somamos custo, déficit de adequação e UP normalizados. Os pesos NÃO são uma descoberta científica. Método compensatório: uma vantagem pode compensar uma desvantagem. Regras inegociáveis são filtros, antes da pontuação.'),
('code', """cost_priority = choose_weighted(front3,(.7,.2,.1))
health_priority = choose_weighted(front3,(.1,.7,.2))
rule = aspiration(front3,budget=6,minimum_adequacy=66)
for label,r in [('Priorizar custo',cost_priority),('Priorizar adequação',health_priority)]:
    m=r['menu'];print(label,'pesos',r['weights'],'menu',m['foods'],'custo',m['cost'],'adequação',round(m['adequacy'],2),'UP',m['ultra'])
print('Filtro orçamento <= 6 e adequação >= 66%, depois menor UP:',rule)
save('decision.json',dict(menus=menus,front2=front2,front3=front3,cost_priority=cost_priority,health_priority=health_priority,aspiration=rule))"""),
]),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generate-only',action='store_true')
    args = parser.parse_args()
    target = ROOT/'notebooks'
    target.mkdir(exist_ok=True)
    # A temporary kernel specification binds execution to this exact interpreter.
    with tempfile.TemporaryDirectory(prefix='latinoware-kernel-') as tmp:
        kernel = Path(tmp)/'kernels/latinoware-local'
        kernel.mkdir(parents=True)
        (kernel/'kernel.json').write_text(json.dumps(dict(argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],display_name='Latinoware Python',language='python')),encoding='utf-8')
        previous = os.environ.get('JUPYTER_PATH')
        os.environ['JUPYTER_PATH'] = tmp + (os.pathsep+previous if previous else '')
        try:
            for filename, title, cells in NOTEBOOKS:
                doc = notebook(title,cells)
                if not args.generate_only:
                    NotebookClient(doc,timeout=180,kernel_name='latinoware-local',resources={'metadata':{'path':str(ROOT)}}).execute()
                nb.write(doc,target/filename)
                print(('Generated' if args.generate_only else 'Executed')+': '+filename,flush=True)
        finally:
            if previous is None: os.environ.pop('JUPYTER_PATH',None)
            else: os.environ['JUPYTER_PATH']=previous
    if not args.generate_only:
        result = dict(date='2026-10-09',python=platform.python_version(),platform=platform.platform(),
                      versions={m:version(m) for m in ['pulp','numpy','matplotlib','networkx','nbformat','nbclient']},
                      notebooks={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(target.glob('*.ipynb'))},
                      source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                                     [ROOT/'optimization_examples/selection.py',ROOT/'optimization_examples/menu_decision.py',Path(__file__)]},
                      data_status='Synthetic; no TBCA data or derived fixtures',timing_scope='One execution; solver time limits and elapsed times differ; hardware dependent')
        (ROOT/'results/sequence/execution.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__ == '__main__':
    main()
