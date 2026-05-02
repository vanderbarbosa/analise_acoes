"""Agrega scores individuais de notícias num único `news_score` por ticker/dia."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import select

from config import CATEGORY_WEIGHT
from src.db.models import NewsRaw, NewsScored, Ticker, session_scope


def aggregate_for(symbol: str, on_date: date) -> float:
    """Lê notícias scoradas dos últimos 2 dias e devolve score [-1, 1] ponderado.
    Usa janela de 48h para capturar efeito tardio do mercado.
    """
    since = datetime.combine(on_date - timedelta(days=2), datetime.min.time())
    until = datetime.combine(on_date + timedelta(days=1), datetime.min.time())

    with session_scope() as session:
        ticker = session.scalar(select(Ticker).where(Ticker.symbol == symbol))
        if ticker is None:
            return 0.0
        rows = session.execute(
            select(NewsScored, NewsRaw)
            .join(NewsRaw, NewsRaw.id == NewsScored.news_id)
            .where(NewsScored.ticker_id == ticker.id)
            .where(NewsRaw.published >= since)
            .where(NewsRaw.published < until)
        ).all()

    if not rows:
        return 0.0

    weighted_sum = 0.0
    weight_total = 0.0
    for scored, _news in rows:
        cat_w = CATEGORY_WEIGHT.get(scored.category, 0.0)
        weight = cat_w * scored.relevance
        if weight <= 0:
            continue
        weighted_sum += scored.sentiment * weight
        weight_total += weight

    if weight_total == 0:
        return 0.0
    return max(-1.0, min(1.0, weighted_sum / weight_total))
