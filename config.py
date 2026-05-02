"""Configurações globais do sistema."""
from __future__ import annotations

from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
MODELS_DIR = DATA_DIR / "models"

DATABASE_URL = f"sqlite:///{DATA_DIR / 'analise.db'}"

# Tickers seguidos. Sufixo .SA = B3 no yfinance.
TICKERS: dict[str, str] = {
    "PETR4": "PETR4.SA",
    "VALE3": "VALE3.SA",
    "ITUB4": "ITUB4.SA",
}

# Janela de backfill inicial.
BACKFILL_START = date(2026, 1, 1)
BACKFILL_END = date(2026, 3, 31)

# Janela de histórico para indicadores técnicos (precisa de bagagem antes do start).
PRICE_LOOKBACK_DAYS = 200

# Pesos do projector (configuráveis sem mexer no código).
WEIGHT_NEWS = 0.55
WEIGHT_TECHNICAL = 0.45

# Threshold mínimo de relevância para manter notícia.
NEWS_RELEVANCE_THRESHOLD = 0.4

# Categorias de notícia (usadas no zero-shot).
NEWS_CATEGORIES: dict[str, str] = {
    "macroeconomica": (
        "notícia macroeconômica sobre câmbio, juros, inflação, "
        "commodities, PIB ou política monetária"
    ),
    "politica": (
        "notícia política sobre governo, regulação, eleições, "
        "ministérios ou decisões do congresso"
    ),
    "fundamentos": (
        "notícia sobre fundamentos da empresa: balanço, lucro, dividendos, "
        "fusão, aquisição, dívida ou guidance"
    ),
    "outro": "notícia não relacionada a economia ou empresa",
}

# Pesos por categoria no agregado de notícias.
CATEGORY_WEIGHT: dict[str, float] = {
    "fundamentos": 1.0,
    "macroeconomica": 0.7,
    "politica": 0.5,
    "outro": 0.0,
}

# Fontes RSS (free).
NEWS_FEEDS: list[dict[str, str]] = [
    {"name": "InfoMoney", "url": "https://www.infomoney.com.br/feed/"},
    {"name": "Money Times", "url": "https://www.moneytimes.com.br/feed/"},
    {"name": "G1 Economia", "url": "https://g1.globo.com/dynamo/economia/rss2.xml"},
]

# Regex de menção por ticker (usado pelo filter).
TICKER_PATTERNS: dict[str, str] = {
    "PETR4": r"(?i)\b(petrobras|petr[34]|pn\s*petrobras)\b",
    "VALE3": r"(?i)\b(vale\s+s\.?a\.?|vale3|mineradora\s+vale)\b",
    "ITUB4": r"(?i)\b(ita[uú]\s*unibanco|itau|itub[34])\b",
}

# Credibilidade da fonte (usado no score de relevância).
SOURCE_CREDIBILITY: dict[str, float] = {
    "InfoMoney": 0.9,
    "Money Times": 0.85,
    "G1 Economia": 0.8,
    "default": 0.6,
}

# Indicadores técnicos.
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
EMA_PERIODS = (9, 21, 50)
BB_PERIOD = 20
BB_STD = 2.0
ATR_PERIOD = 14
