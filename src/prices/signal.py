"""Converte indicadores técnicos em um score normalizado [-1, 1]."""
from __future__ import annotations

import math

import pandas as pd


def _clip(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    if math.isnan(x):
        return 0.0
    return max(lo, min(hi, x))


def technical_score(row: pd.Series) -> float:
    """Combina RSI, MACD-hist e posição vs EMAs/Bollinger num único score [-1,1].

    Heurística simples (não treinada):
      - RSI < 30 → +0.5 (sobrevendido), RSI > 70 → -0.5 (sobrecomprado), linear no meio
      - MACD hist > 0 → bullish proporcional ao tamanho normalizado pelo close
      - Close > EMA21 → +0.3, < EMA21 → -0.3
      - Close acima da banda superior → -0.2, abaixo da inferior → +0.2
    Pesos somados e clipados.
    """
    score = 0.0
    close = float(row.get("close", float("nan")))

    rsi = row.get("rsi")
    if rsi is not None and not pd.isna(rsi):
        if rsi < 30:
            score += 0.5
        elif rsi > 70:
            score -= 0.5
        else:
            score += (50.0 - float(rsi)) / 40.0 * 0.3

    hist = row.get("macd_hist")
    if hist is not None and not pd.isna(hist) and close and not math.isnan(close):
        norm = float(hist) / close * 100.0
        score += _clip(norm, -1.0, 1.0) * 0.4

    ema21 = row.get("ema_21")
    if ema21 is not None and not pd.isna(ema21) and close:
        score += 0.3 if close > float(ema21) else -0.3

    bb_up = row.get("bb_upper")
    bb_lo = row.get("bb_lower")
    if bb_up is not None and not pd.isna(bb_up) and close > float(bb_up):
        score -= 0.2
    if bb_lo is not None and not pd.isna(bb_lo) and close < float(bb_lo):
        score += 0.2

    return _clip(score)
