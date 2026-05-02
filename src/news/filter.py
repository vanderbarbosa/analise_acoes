"""Filtra notícias: detecta menções por ticker via regex e calcula relevância."""
from __future__ import annotations

import re
from typing import Iterable

from config import NEWS_RELEVANCE_THRESHOLD, SOURCE_CREDIBILITY, TICKER_PATTERNS

_COMPILED = {symbol: re.compile(pattern) for symbol, pattern in TICKER_PATTERNS.items()}


def detect_tickers(text: str) -> list[str]:
    if not text:
        return []
    return [symbol for symbol, regex in _COMPILED.items() if regex.search(text)]


def relevance_for(symbol: str, source: str, text: str) -> float:
    """Score 0..1 baseado em número de menções, posição (título vale mais) e
    credibilidade da fonte. Não usa NLP."""
    if not text:
        return 0.0
    regex = _COMPILED.get(symbol)
    if regex is None:
        return 0.0
    matches = len(regex.findall(text))
    if matches == 0:
        return 0.0
    base = min(0.4 + 0.15 * matches, 0.85)
    source_weight = SOURCE_CREDIBILITY.get(source, SOURCE_CREDIBILITY["default"])
    return min(base * source_weight + 0.1, 1.0)


def filter_relevant(items: Iterable[dict]) -> list[tuple[dict, str, float]]:
    """Retorna lista (item, ticker, relevance) só com relevância >= threshold."""
    out: list[tuple[dict, str, float]] = []
    for item in items:
        text = f"{item.get('title', '')}. {item.get('summary', '')}"
        for symbol in detect_tickers(text):
            r = relevance_for(symbol, item.get("source", ""), text)
            if r >= NEWS_RELEVANCE_THRESHOLD:
                out.append((item, symbol, r))
    return out
