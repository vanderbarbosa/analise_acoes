# Análise de Ações — PETR4 / VALE3 / ITUB4

Site em Python que coleta notícias diárias, classifica por categoria
(macroeconômica / política / fundamentos), combina com análise técnica do
histórico de preço e gera uma projeção do próximo pregão (direção + magnitude).

> ⚠️ Este projeto é apoio à decisão / estudo. **Não é recomendação de
> investimento.** Modelos realistas de previsão de direção diária de ações
> acertam ~52-58% dos casos.

## Setup

```powershell
cd D:\PROJETOS\analise_acoes
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -c "from src.db.models import init_db; init_db()"
```

## Backfill Q1 2026 (técnico)

```powershell
python -m src.jobs.backfill
```

## Subir o site

```powershell
python app.py
```

Abre em `http://localhost:5000`.

## Estrutura

- `src/news/` — coleta, classifica e filtra notícias (NLP local)
- `src/prices/` — preços e indicadores técnicos (yfinance + pandas-ta)
- `src/prediction/` — combina sinais e gera projeção
- `src/db/` — schema SQLAlchemy + SQLite
- `src/jobs/` — pipeline diário e backfill histórico
- `templates/` — Jinja2
- `data/` — banco SQLite e cache de modelos
