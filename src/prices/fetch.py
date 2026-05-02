"""Download de OHLCV via yfinance."""
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import yfinance as yf

from config import PRICE_LOOKBACK_DAYS


def fetch_ohlcv(yahoo_symbol: str, start: date, end: date) -> pd.DataFrame:
    """Baixa OHLCV diário do Yahoo. Inclui um lookback antes de `start` para
    permitir cálculo de indicadores que precisam de janela.
    Retorna DataFrame indexado por data com colunas open/high/low/close/volume.
    """
    real_start = start - timedelta(days=PRICE_LOOKBACK_DAYS)
    real_end = end + timedelta(days=1)
    df = yf.download(
        yahoo_symbol,
        start=real_start.isoformat(),
        end=real_end.isoformat(),
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=False,
    )
    if df is None or df.empty:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.rename(columns=str.lower)
    df = df[["open", "high", "low", "close", "volume"]].copy()
    df.index = pd.to_datetime(df.index).date
    df.index.name = "trade_date"
    return df.dropna(subset=["close"])
