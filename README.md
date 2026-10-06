# Latinoware Optimization Examples

Exemplos executáveis para a palestra **Como Formular e Resolver Problemas Complexos** (Latinoware 2026).

Os exemplos acompanham o ciclo da palestra: formulação linear de uma dieta ilustrativa, teste de viabilidade e folgas, modelo inteiro e heurística. Valores nutricionais e custos dos exemplos são sintéticos e didáticos; não são recomendação alimentar nem dados de mercado.

## Ambiente

Python 3.10 ou superior.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python examples\diet_lp.py
python examples\diet_milp.py
python examples\feasibility.py
python examples\relaxation.py
python examples\greedy_heuristic.py
```

`diet_lp.py` e `diet_milp.py` usam PuLP com CBC e incluem limites artificiais de emissão. `relaxation.py` compara uma mochila inteira com a relaxação LP. Os exemplos identificam resultados artificiais como sintéticos; consulte `data/foods.csv`.
