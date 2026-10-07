# Latinoware — exemplos de otimização

Código da palestra **Como Formular e Resolver Problemas Complexos**, 60 minutos.

## Instalação

Python 3.11 ou superior; execução registrada com Python 3.14, PuLP/CBC, NetworkX e pymoo. As versões exatas e hashes dos dados estão em [results/demo-results.json](results/demo-results.json); dependências resolvidas em `requirements.lock.txt`.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Exemplos do roteiro atual

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
