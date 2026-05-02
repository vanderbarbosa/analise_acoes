"""Coletor de notícias via RSS."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

import feedparser

from config import NEWS_FEEDS


def _parse_published(entry) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed"):
        value = getattr(entry, attr, None)
        if value:
            try:
                return datetime(*value[:6], tzinfo=timezone.utc)
            except (TypeError, ValueError):
                continue
    return None


def collect_all() -> Iterable[dict]:
    """Itera por todos os feeds configurados e devolve dicts normalizados.
    Campos: source, title, link, summary, published.
    """
    for feed_cfg in NEWS_FEEDS:
        parsed = feedparser.parse(feed_cfg["url"])
        for entry in parsed.entries:
            link = getattr(entry, "link", None)
            title = getattr(entry, "title", None)
            if not link or not title:
                continue
            yield {
                "source": feed_cfg["name"],
                "title": title.strip(),
                "link": link.strip(),
                "summary": (getattr(entry, "summary", "") or "").strip(),
                "published": _parse_published(entry),
            }
