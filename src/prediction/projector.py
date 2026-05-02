"""Combina news_score e tech_score numa projeção do próximo pregão."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import desc, select

from config import WEIGHT_NEWS, WEIGHT_TECHNICAL
from src.db.models import PriceDaily, Ticker, session_scope


@dataclass
class Projection:
    direction: str  # "alta" | "baixa" | "neutro"
    magnitude_pct: float
    confidence: float
    news_score: float
    tech_score: float
    combined_score: float
    rationale: str


def _direction(score: float) -> str:
    if score > 0.15:
        return "alta"
    if score < -0.15:
        return "baixa"
    return "neutro"


def project(
    symbol: str,
    on_date: date,
    news_score: float,
    tech_score: float,
) -> Projection:
    """Gera projeção para `on_date + 1 pregão`. Magnitude estimada por ATR%
    do último candle disponível, escalada pela confiança.
    """
    combined = news_score * WEIGHT_NEWS + tech_score * WEIGHT_TECHNICAL
    direction = _direction(combined)

    with session_scope() as session:
        ticker = session.scalar(select(Ticker).where(Ticker.symbol == symbol))
        atr_pct = 1.0
        if ticker is not None:
            last = session.scalar(
                select(PriceDaily)
                .where(PriceDaily.ticker_id == ticker.id)
                .where(PriceDaily.trade_date <= on_date)
                .order_by(desc(PriceDaily.trade_date))
                .limit(1)
            )
            if last and last.atr and last.close:
                atr_pct = (last.atr / last.close) * 100.0

    confidence = min(abs(combined), 1.0)
    magnitude = atr_pct * (0.4 + 0.6 * confidence)
    if direction == "neutro":
        magnitude *= 0.3

    rationale = (
        f"news={news_score:+.2f} (peso {WEIGHT_NEWS}), "
        f"técnico={tech_score:+.2f} (peso {WEIGHT_TECHNICAL}), "
        f"combinado={combined:+.2f}, ATR%={atr_pct:.2f}"
    )
    return Projection(
        direction=direction,
        magnitude_pct=magnitude,
        confidence=confidence,
        news_score=news_score,
        tech_score=tech_score,
        combined_score=combined,
        rationale=rationale,
    )


def next_business_day(d: date) -> date:
    nxt = d + timedelta(days=1)
    while nxt.weekday() >= 5:
        nxt += timedelta(days=1)
    return nxt
