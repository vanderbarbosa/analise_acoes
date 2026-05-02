"""Indicadores técnicos em pandas puro."""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import (
    ATR_PERIOD,
    BB_PERIOD,
    BB_STD,
    EMA_PERIODS,
    MACD_FAST,
    MACD_SIGNAL,
    MACD_SLOW,
    RSI_PERIOD,
)


def _rsi(close: pd.Series, period: int = RSI_PERIOD) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    return 100.0 - (100.0 / (1.0 + rs))


def _macd(close: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    ema_fast = close.ewm(span=MACD_FAST, adjust=False).mean()
    ema_slow = close.ewm(span=MACD_SLOW, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal = macd.ewm(span=MACD_SIGNAL, adjust=False).mean()
    hist = macd - signal
    return macd, signal, hist


def _bollinger(close: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    mid = close.rolling(BB_PERIOD).mean()
    std = close.rolling(BB_PERIOD).std(ddof=0)
    upper = mid + BB_STD * std
    lower = mid - BB_STD * std
    return upper, mid, lower


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = ATR_PERIOD) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            (high - low).abs(),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona colunas de RSI, MACD, EMAs, Bollinger e ATR ao DF de OHLCV."""
    if df.empty:
        return df

    out = df.copy()
    close = out["close"]

    out["rsi"] = _rsi(close)
    macd, signal, hist = _macd(close)
    out["macd"] = macd
    out["macd_signal"] = signal
    out["macd_hist"] = hist

    for n in EMA_PERIODS:
        out[f"ema_{n}"] = close.ewm(span=n, adjust=False).mean()

    upper, mid, lower = _bollinger(close)
    out["bb_upper"] = upper
    out["bb_mid"] = mid
    out["bb_lower"] = lower

    out["atr"] = _atr(out["high"], out["low"], close)
    return out
