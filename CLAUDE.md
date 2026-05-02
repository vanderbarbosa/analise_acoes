# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project purpose

Flask site that tracks PETR4, VALE3 and ITUB4 on B3. Pulls daily news via RSS, classifies each article (macro / política / fundamentos), combines that with technical indicators on the price history (yfinance), and emits a next-trading-day projection (direction + magnitude + confidence). Disclaimer in the UI: study/decision-support, not investment advice. Realistic ceiling for daily directional accuracy is ~52–58%.

## Commands

The project uses a venv local to the repo at `.venv\`. Always invoke via `.\.venv\Scripts\python.exe` rather than the system `python`.

```powershell
# Setup
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Bootstrap DB and seed tickers
.\.venv\Scripts\python.exe -X utf8 -c "from src.db.models import init_db; init_db()"

# Backfill prices+indicators for the BACKFILL_START..END window in config.py
.\.venv\Scripts\python.exe -X utf8 -m src.jobs.backfill

# Daily pipeline: ingest RSS, score, refresh today's prices, generate prediction
.\.venv\Scripts\python.exe -X utf8 -m src.jobs.daily

# Run the site
.\.venv\Scripts\python.exe -X utf8 app.py        # http://127.0.0.1:5000

# Tests
.\.venv\Scripts\python.exe -m pytest                          # all
.\.venv\Scripts\python.exe -m pytest tests/test_X.py::test_Y  # single test
```

`-X utf8` is required on Windows: console defaults to cp1252 and any print with `→`, `ç`, etc. will crash the job (already happened during initial backfill). All job entry points should be invoked this way.

## Architecture

### Data flow (one pipeline tick)

```
RSS feeds (config.NEWS_FEEDS)
    ↓ src/news/collect.py        (feedparser)
    ↓ src/news/filter.py         (regex per ticker + source credibility → relevance ≥ NEWS_RELEVANCE_THRESHOLD)
    ↓ src/news/classify.py       (heuristic: keywords → category, +/- term ratio → sentiment)
    ↓ persisted to news_raw + news_scored
    ↓ src/news/score.py          (48h window, weighted by CATEGORY_WEIGHT × relevance) → news_score ∈ [-1, 1]

yfinance OHLCV
    ↓ src/prices/fetch.py        (downloads start - PRICE_LOOKBACK_DAYS so EMAs warm up)
    ↓ src/prices/indicators.py   (RSI, MACD, EMAs, Bollinger, ATR — all pure pandas)
    ↓ src/prices/signal.py       (heuristic combiner) → tech_score ∈ [-1, 1]
    ↓ persisted to price_daily

src/prediction/projector.py
    combined = news_score * WEIGHT_NEWS + tech_score * WEIGHT_TECHNICAL    # 0.55 / 0.45 default
    direction = sign of combined (with ±0.15 dead zone → "neutro")
    magnitude_pct = ATR%(last close) * (0.4 + 0.6 * confidence), shrunk for "neutro"
    → persisted to predictions(for_date = next business day)
```

`src/jobs/daily.py` orchestrates the whole tick. `src/jobs/backfill.py` only handles the price half (notícias não fazem sentido para datas históricas via RSS).

### Why these splits

- **`prices/` is split fetch / indicators / signal** so the indicator math stays pure-pandas and unit-testable without hitting yfinance, and the heuristic that turns indicators into a single number is one small file you can swap for a trained model later.
- **`news/` is split collect / filter / classify / score** for the same reason: RSS is the only side-effecting boundary; filter is regex; classify is the *only* place to swap when activating real NLP; score is pure aggregation off the DB.
- **`prediction/projector.py` is intentionally dumb.** All the smarts live in the two scores it consumes — keep it that way so weight changes are a config edit, not a refactor.

### config.py is load-bearing

Tickers, RSS feeds, regex per ticker, source credibility, category weights, indicator periods, `WEIGHT_NEWS`/`WEIGHT_TECHNICAL`, `BACKFILL_START`/`END`, `NEWS_RELEVANCE_THRESHOLD` — all live in `config.py`. Don't hardcode any of these in modules; read them from config so a tweak is one edit.

### DB

SQLite at `data/analise.db`, schema in `src/db/models.py`. `init_db()` is idempotent and also seeds the `tickers` table from `config.TICKERS`. All sessions go through `session_scope()`. Backfill is idempotent: it `DELETE`s the date window before re-inserting.

### NLP is intentionally off

`requirements.txt` keeps `transformers`/`torch`/`sentencepiece` commented out. `src/news/classify.py` is a keyword-list heuristic that respects the same signature (`classify_category(text) -> str`, `score_sentiment(text) -> float`). To activate real NLP, uncomment those deps and replace just those two functions with zero-shot + a PT-BR sentiment model — nothing downstream changes.

### Removed dependency: pandas-ta

`pandas-ta>=0.3.14b` is no longer on PyPI. Indicators are implemented directly in `src/prices/indicators.py` (RSI via Wilder's EMA, MACD via 12/26/9 EWM, Bollinger 20/2σ, ATR via Wilder). Don't re-add `pandas-ta` to `requirements.txt`.

### Flask app

`app.py` defines two routes (`/` and `/ticker/<symbol>`) plus three Jinja filters (`brl`, `pct`, `d`). Charts are server-rendered Plotly via `plotly.io.to_html(..., include_plotlyjs="cdn", full_html=False)` and embedded with `|safe`. Templates extend `templates/base.html`; styles in `static/css/app.css`.
