"""Backfill histórico de preços + indicadores + tech_score."""
from __future__ import annotations

from datetime import date

import pandas as pd
from sqlalchemy import delete, select

from config import BACKFILL_END, BACKFILL_START, TICKERS
from src.db.models import PriceDaily, Ticker, init_db, session_scope
from src.prices.fetch import fetch_ohlcv
from src.prices.indicators import add_indicators
from src.prices.signal import technical_score


def _row_to_kwargs(ticker_id: int, trade_date: date, row: pd.Series) -> dict:
    def opt(name: str):
        v = row.get(name)
        if v is None or pd.isna(v):
            return None
        return float(v)

    return dict(
        ticker_id=ticker_id,
        trade_date=trade_date,
        open=float(row["open"]),
        high=float(row["high"]),
        low=float(row["low"]),
        close=float(row["close"]),
        volume=float(row.get("volume", 0.0) or 0.0),
        rsi=opt("rsi"),
        macd=opt("macd"),
        macd_signal=opt("macd_signal"),
        macd_hist=opt("macd_hist"),
        ema_9=opt("ema_9"),
        ema_21=opt("ema_21"),
        ema_50=opt("ema_50"),
        bb_upper=opt("bb_upper"),
        bb_lower=opt("bb_lower"),
        bb_mid=opt("bb_mid"),
        atr=opt("atr"),
        tech_score=opt("tech_score"),
    )


def backfill_one(symbol: str, start: date = BACKFILL_START, end: date = BACKFILL_END) -> int:
    """Baixa OHLCV, calcula indicadores e grava intervalo [start, end]. Retorna nº de linhas."""
    with session_scope() as session:
        ticker = session.scalar(select(Ticker).where(Ticker.symbol == symbol))
        if ticker is None:
            raise RuntimeError(f"Ticker {symbol} não cadastrado. Rode init_db primeiro.")
        ticker_id = ticker.id
        yahoo_symbol = ticker.yahoo_symbol

    raw = fetch_ohlcv(yahoo_symbol, start, end)
    if raw.empty:
        print(f"[backfill] {symbol}: sem dados retornados pelo yfinance")
        return 0

    enriched = add_indicators(raw)
    enriched["tech_score"] = enriched.apply(technical_score, axis=1)

    in_window = enriched[(enriched.index >= start) & (enriched.index <= end)]

    with session_scope() as session:
        session.execute(
            delete(PriceDaily).where(
                PriceDaily.ticker_id == ticker_id,
                PriceDaily.trade_date >= start,
                PriceDaily.trade_date <= end,
            )
        )
        for trade_date, row in in_window.iterrows():
            session.add(PriceDaily(**_row_to_kwargs(ticker_id, trade_date, row)))
        session.commit()

    print(f"[backfill] {symbol}: {len(in_window)} pregoes gravados ({start} a {end})")
    return len(in_window)


def main() -> None:
    init_db()
    total = 0
    for symbol in TICKERS:
        total += backfill_one(symbol)
    print(f"[backfill] total: {total} linhas em price_daily")


if __name__ == "__main__":
    main()
