"""Job diário: coleta notícias do dia, scora, calcula projeção e grava."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import select

from config import TICKERS
from src.db.models import (
    NewsRaw,
    NewsScored,
    Prediction,
    Ticker,
    init_db,
    session_scope,
)
from src.news.classify import classify_category, score_sentiment
from src.news.collect import collect_all
from src.news.filter import filter_relevant
from src.news.score import aggregate_for
from src.prediction.projector import next_business_day, project
from src.prices.signal import technical_score
from src.prices.indicators import add_indicators
from src.prices.fetch import fetch_ohlcv
from src.jobs.backfill import backfill_one


def ingest_news() -> int:
    """Coleta RSS, persiste novas e scora por ticker."""
    items = list(collect_all())
    if not items:
        print("[daily] nenhuma notícia coletada")
        return 0

    relevant = filter_relevant(items)
    inserted = 0
    with session_scope() as session:
        ticker_map = {t.symbol: t.id for t in session.scalars(select(Ticker)).all()}

        link_to_news_id: dict[str, int] = {}
        for item, _symbol, _rel in relevant:
            link = item["link"]
            if link in link_to_news_id:
                continue
            existing = session.scalar(select(NewsRaw).where(NewsRaw.link == link))
            if existing is not None:
                link_to_news_id[link] = existing.id
                continue
            news = NewsRaw(
                source=item["source"],
                title=item["title"][:512],
                link=link[:1024],
                summary=item.get("summary"),
                published=item.get("published") or datetime.utcnow(),
                fetched_at=datetime.utcnow(),
            )
            session.add(news)
            session.flush()
            link_to_news_id[link] = news.id
            inserted += 1

        for item, symbol, relevance in relevant:
            news_id = link_to_news_id.get(item["link"])
            if news_id is None:
                continue
            ticker_id = ticker_map.get(symbol)
            if ticker_id is None:
                continue
            existing_score = session.scalar(
                select(NewsScored).where(
                    NewsScored.news_id == news_id,
                    NewsScored.ticker_id == ticker_id,
                )
            )
            if existing_score is not None:
                continue
            text = f"{item['title']}. {item.get('summary') or ''}"
            category = classify_category(text)
            sentiment = score_sentiment(text)
            session.add(
                NewsScored(
                    news_id=news_id,
                    ticker_id=ticker_id,
                    category=category,
                    relevance=relevance,
                    sentiment=sentiment,
                    impact=relevance * abs(sentiment),
                )
            )
        session.commit()

    print(f"[daily] notícias novas: {inserted}; scoradas (relevante): {len(relevant)}")
    return inserted


def refresh_today_prices(today: date) -> None:
    """Garante que o pregão de hoje (ou último útil) está no banco com indicadores."""
    for symbol in TICKERS:
        backfill_one(symbol, start=today.replace(day=1), end=today)


def generate_predictions(today: date) -> int:
    """Para cada ticker, calcula news_score+tech_score do dia e grava prediction
    para o próximo pregão."""
    target = next_business_day(today)
    saved = 0

    with session_scope() as session:
        tickers = list(session.scalars(select(Ticker)).all())

    for ticker in tickers:
        with session_scope() as session:
            from src.db.models import PriceDaily
            from sqlalchemy import desc as _desc

            last = session.scalar(
                select(PriceDaily)
                .where(PriceDaily.ticker_id == ticker.id)
                .where(PriceDaily.trade_date <= today)
                .order_by(_desc(PriceDaily.trade_date))
                .limit(1)
            )
        tech = float(last.tech_score) if last and last.tech_score is not None else 0.0
        news = aggregate_for(ticker.symbol, today)
        proj = project(ticker.symbol, today, news, tech)

        with session_scope() as session:
            existing = session.scalar(
                select(Prediction).where(
                    Prediction.ticker_id == ticker.id,
                    Prediction.for_date == target,
                )
            )
            if existing is not None:
                existing.direction = proj.direction
                existing.magnitude_pct = proj.magnitude_pct
                existing.confidence = proj.confidence
                existing.news_score = proj.news_score
                existing.tech_score = proj.tech_score
                existing.combined_score = proj.combined_score
                existing.rationale = proj.rationale
                existing.generated_at = datetime.utcnow()
            else:
                session.add(
                    Prediction(
                        ticker_id=ticker.id,
                        for_date=target,
                        direction=proj.direction,
                        magnitude_pct=proj.magnitude_pct,
                        confidence=proj.confidence,
                        news_score=proj.news_score,
                        tech_score=proj.tech_score,
                        combined_score=proj.combined_score,
                        rationale=proj.rationale,
                    )
                )
            session.commit()
            saved += 1

    print(f"[daily] previsões geradas para {target}: {saved}")
    return saved


def run(today: date | None = None) -> None:
    init_db()
    today = today or date.today()
    ingest_news()
    refresh_today_prices(today)
    generate_predictions(today)


if __name__ == "__main__":
    run()
