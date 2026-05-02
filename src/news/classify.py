"""Classificação heurística por palavras-chave (categoria + sentimento).

Versão sem dependência de transformers — quando o pipeline NLP for ativado,
basta substituir `classify_category` e `score_sentiment` pelas funções equivalentes
baseadas em zero-shot e modelo de sentimento PT-BR.
"""
from __future__ import annotations

import re
import unicodedata

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "macroeconomica": [
        "selic", "juros", "ipca", "inflacao", "cambio", "dolar", "pib",
        "copom", "commodit", "minerio", "petroleo", "fed", "bce",
    ],
    "politica": [
        "governo", "lula", "congresso", "stf", "ministro", "ministerio",
        "regulacao", "eleicao", "reforma", "tribunal", "sancion", "veto",
    ],
    "fundamentos": [
        "balanco", "lucro", "prejuizo", "ebitda", "dividendo", "guidance",
        "fusao", "aquisicao", "divida", "buyback", "follow-on", "ipo",
        "investimento", "capex", "produc",
    ],
}

POSITIVE_TERMS = [
    "alta", "subiu", "ganho", "lucro", "recorde", "supera", "expansao",
    "crescimento", "valoriza", "otimismo", "forte", "supero", "melhora",
    "aprovado", "novo contrato", "reduz divida",
]

NEGATIVE_TERMS = [
    "queda", "caiu", "prejuizo", "perda", "frustra", "abaixo", "recessao",
    "demissao", "rebaixa", "downgrade", "sancao", "multa", "investigacao",
    "greve", "acidente", "vazamento", "aumento de divida", "rebaixou",
]


def _normalize(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text.lower()


def classify_category(text: str) -> str:
    norm = _normalize(text)
    counts = {cat: 0 for cat in CATEGORY_KEYWORDS}
    for cat, kws in CATEGORY_KEYWORDS.items():
        for kw in kws:
            if kw in norm:
                counts[cat] += 1
    best_cat = max(counts, key=counts.get)
    if counts[best_cat] == 0:
        return "outro"
    return best_cat


def score_sentiment(text: str) -> float:
    """Sentimento [-1, 1] por contagem de termos positivos vs negativos."""
    norm = _normalize(text)
    pos = sum(1 for term in POSITIVE_TERMS if term in norm)
    neg = sum(1 for term in NEGATIVE_TERMS if term in norm)
    total = pos + neg
    if total == 0:
        return 0.0
    raw = (pos - neg) / total
    return max(-1.0, min(1.0, raw))
