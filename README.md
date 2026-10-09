# Latinoware — exemplos de otimização

Código da palestra **Como Formular e Resolver Problemas Complexos**, 60 minutos.

## Instalação

Python 3.11 ou superior para as dependências abertas; execução arquivada/lock com Python 3.14. Versões e hashes dos notebooks em [results/sequence/execution.json](results/sequence/execution.json). Resultados do roteiro anterior: [results/demo-results.json](results/demo-results.json). Para reconstruir o ambiente arquivado, use Python 3.14 e `requirements.lock.txt`.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Notebooks do roteiro atual

| Notebook | Conteúdo |
|---|---|
| [01_problemas.ipynb](notebooks/01_problemas.ipynb) | if/else, menor caminho e hipótese de enumeração de rotas |
| [02_formulacao.ipynb](notebooks/02_formulacao.ipynb) | Seis kits: variáveis, objetivo, restrições e enumeração |
| [03_solver_e_limites.ipynb](notebooks/03_solver_e_limites.ipynb) | CBC no caso pequeno e limite de tempo no estresse |
| [04_relaxamentos.ipynb](notebooks/04_relaxamentos.ipynb) | Limite LP, arredondamento e meta inviável flexibilizada |
| [05_algoritmo_genetico.ipynb](notebooks/05_algoritmo_genetico.ipynb) | Operadores, reparo, elitismo, saída e evolução da prioridade |
| [06_pareto_e_decisao.ipynb](notebooks/06_pareto_e_decisao.ipynb) | 81 menus, Pareto 2D/3D, pesos e metas de aspiração |

Todos têm células e outputs de execução real. Abra no Jupyter/VS Code e selecione o Python da `.venv`. Reconstrução completa, da raiz de `codes`:

```powershell
python tools/build_talk_notebooks.py
python tools/export_sequence_slides.py --presentation ../presentation
```

O primeiro script executa os notebooks com um kernel temporário ligado ao mesmo interpretador. O segundo copia figuras, macros numéricas e resumo do log real para o LaTeX. `--generate-only` gera notebooks sem outputs e não produz a entrega executada. Ao reexecutar, confira se o caso de estresse voltou a encerrar sem certificado antes de narrá-lo dessa forma.

### Dados e interpretação dos exemplos novos

- Kits: coeficientes sintéticos em `optimization_examples/selection.py`. Seis itens/duas capacidades; estresse de 250 itens/dez recursos artificiais, semente 2026. Prioridade não é impacto social medido. CBC padrão, sem threads adicionais; conferir `sol_status`, log e capacidades.
- Caso pequeno: solver e 64 configurações enumeradas concordam em prioridade 36; LP fornece limite superior 36,384615. Exigir prioridade mínima 50 é inviável; flexibilizá-la dá déficit 14, preservando capacidades.
- Estresse arquivado: CBC para no limite de 0,3 s com prioridade 5646; LP fornece 5681,626235; construção gulosa 5453 e AG 5621. AG: população 50/30 gerações. Uma execução, orçamentos diferentes; não é benchmark estatístico.
- AG: bits, torneio, cruzamento uniforme, mutação, reparo e elitismo. O reparo garante capacidades neste modelo de limites superiores positivos; não é um reparador universal.
- Cardápios: 81 combinações, três alvos inventados, nenhuma com 100% de adequação. Adequação é a fração de alvos atingidos; UP é participação em energia fictícia. Fronteira exata apenas da grade: quatro cardápios em 2D, seis em 3D. Sem TBCA, recomendação alimentar ou conformidade integral com PNAE.
- Decisão: normalizar custo, déficit de adequação e UP pelos extremos dos seis candidatos. Pesos (0,7;0,2;0,1) escolhem custo 3,50/adequação 33,3%/UP 56,8%; pesos (0,1;0,7;0,2) escolhem 6,10/66,7%/0%. Filtro de orçamento 6 e dois alvos, seguido de menor UP: 5,60/66,7%/31,8%.

## Exemplos complementares do roteiro anterior

Execute da raiz deste repositório:

```powershell
python examples/van_route.py --students 5
python examples/van_route.py --students 15 --windows --time-limit 5
python examples/van_route.py --students 5 --relax
python examples/van_route.py --students 5 --impossible
python examples/route_heuristics.py --students 15 --windows --traffic-factor 1.8
python examples/irrigation.py --water-budget 180000
python examples/irrigation.py --water-budget 40000
python examples/irrigation.py --water-budget 40000 --soft-orders
python examples/irrigation.py --integer
python examples/school_menu.py --method milp
python examples/school_menu.py --method nsga2 --seed 2026 --generations 80
python examples/school_menu.py --method enumerate
python examples/slm_modeling.py --dry-run
```

| Exemplo | Decisão | Método / interpretação |
|---|---|---|
| Van/delivery | Ordem de embarque, garagem → IFCE | TSP aberto, PuLP/CBC + MTZ; NetworkX armazena o grafo |
| Janelas e trânsito | Embarques após 18h30 e chegada até 19h | Modelo determinístico com espera; auditoria de cenário mais lento |
| Heurística de rota | Construir e melhorar uma ordem | Vizinho mais próximo + 2-opt, sem certificado de ótimo |
| Água/agricultura | Hectares por cultura | LP; opção de blocos inteiros; seca e flexibilização de pedidos |
| Merenda | Porções e compras | MILP de custo; NSGA-II com quatro objetivos; referência enumerada |
| SLM | Rascunho de formulação | Prompt revisável; chamada local opcional, sem execução de código gerado |

## Dados e hipóteses

Todos os coeficientes são **sintéticos**. Não há valores restritos da TBCA, preços reais, cota atual do Castanhão ou recomendações nutricionais.

- `data/van_stops.csv`: coordenadas em km, semente 2026; distância euclidiana, 40 km/h, 1 min de embarque, saída às 17h50. Um veículo com capacidade suficiente. Nas janelas, os três primeiros alunos só embarcam após 18h30 e todos até 18h55. Multiplicar tempos por 1,8 é um cenário de estresse, sem probabilidades ou otimização robusta.
- `data/crops.csv`: lucro, água e capital por hectare, limites de mercado e pedidos mínimos. Terra ≤100 ha, capital ≤R$250 mil. Flexibilizar pedidos preserva a água física; primeiro minimiza a soma de hectares não atendidos e depois maximiza lucro. Esse critério não pondera pedidos por cultura.
- `data/school_foods.csv`: seis alimentos, porções fictícias de 50 g. Um cardápio representativo para 100 refeições; bloco fictício de R$600 integralmente FNDE. Compra familiar mínima R$270 = 45% desse bloco, conforme a regra vigente em 2026. O valor não é repasse per capita oficial. Regras adicionais de uma rede PNAE real, oferta, aceitação e nutrição por idade não estão modeladas.

No menu, as faixas obrigatórias ilustrativas são 450–650 kcal, 18–40 g de proteína, 5–20 g de fibra e 150–600 mg de cálcio. Os alvos de 550 kcal, 28 g, 10 g e 200 mg produzem o desvio médio normalizado `mean(abs(nutrient-target)/target)`. Objetivos: minimizar custo, desvio e carbono e maximizar compra familiar. O desvio não é um índice clínico. Rótulo de fornecedor é uma hipótese do dado, não uma certificação real.

## Auditoria e figuras

```powershell
python tools/build_demo_artifacts.py
# No projeto coordenador, para atualizar as figuras dos slides:
.\codes\.venv\Scripts\python.exe codes/tools/build_demo_artifacts.py --figures presentation/figs
```

O script confere a rota de 5 alunos contra 120 permutações, limite LP, horários, caso impossível, seca, restrições físicas, menus e referência enumerada. Salva relatório JSON, CSV e três figuras PDF. Os tempos dependem da máquina e de uma execução; o limite CBC não inclui construção do modelo. O CBC usa execução padrão sem threads adicionais, evitando o bloqueio observado com threads explícitas no Windows.

Resultados registrados: rota de 15 alunos ótima de 19,8078 km; com janelas, candidato CBC viável de 35,0491 km sem prova concluída; heurística com janelas 25,1399 km. Não confundir o status PuLP com certificado: também verificamos `sol_status` e recalculamos a rota.

Menu: 15.625 combinações, 507 viáveis, 150 não dominadas. NSGA-II retorna 120 candidatos viáveis; encontra 118 vetores da referência e dois candidatos dominados pela grade. Essa referência é exata somente para o pequeno espaço discreto; não prova qualidade em uma rede escolar real. `menu-front.csv` conserva os quatro objetivos, embora o gráfico mostre uma projeção.

Para inferência opcional, instale Ollama e um modelo local, inicie o serviço e execute `python examples/slm_modeling.py --model NOME_INSTALADO`. Apenas `--dry-run` foi verificado nesta entrega; não houve inferência, benchmark ou validação de saída de SLM.

Os cinco scripts de dieta da primeira versão estão em `examples/legacy/`; não fazem parte do roteiro atual.
