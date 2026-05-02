"""Flask app: home com tickers + página de detalhe."""
from __future__ import annotations

from datetime import date, timedelta

import plotly.graph_objects as go
from flask import Flask, abort, render_template
from plotly.io import to_html
from sqlalchemy import desc, select

from config import TICKERS
from src.db.models import (
    NewsRaw,
    NewsScored,
    PriceDaily,
    Prediction,
    Ticker,
    init_db,
    session_scope,
)

app = Flask(__name__)


def _latest_prediction(session, ticker_id: int):
    return session.scalar(
        select(Prediction)
        .where(Prediction.ticker_id == ticker_id)
        .order_by(desc(Prediction.for_date), desc(Prediction.generated_at))
        .limit(1)
    )


@app.route("/")
def home():
    rows = []
    with session_scope() as session:
        tickers = list(session.scalars(select(Ticker).order_by(Ticker.symbol)).all())
        for t in tickers:
            last_price = session.scalar(
                select(PriceDaily)
                .where(PriceDaily.ticker_id == t.id)
                .order_by(desc(PriceDaily.trade_date))
                .limit(1)
            )
            pred = _latest_prediction(session, t.id)
            rows.append({
                "symbol": t.symbol,
                "name": t.name or t.symbol,
                "last_close": last_price.close if last_price else None,
                "last_date": last_price.trade_date if last_price else None,
                "prediction": pred,
            })
    return render_template("index.html", rows=rows, tickers=TICKERS)


def _build_chart(prices: list[PriceDaily]) -> str:
    if not prices:
        return "<p>Sem dados de preço para exibir.</p>"
    dates = [p.trade_date for p in prices]
    closes = [p.close for p in prices]
    ema21 = [p.ema_21 for p in prices]
    ema50 = [p.ema_50 for p in prices]
    bb_up = [p.bb_upper for p in prices]
    bb_lo = [p.bb_lower for p in prices]

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=dates,
        open=[p.open for p in prices],
        high=[p.high for p in prices],
        low=[p.low for p in prices],
        close=closes,
        name="OHLC",
        showlegend=False,
    ))
    fig.add_trace(go.Scatter(x=dates, y=ema21, mode="lines", name="EMA 21",
                             line=dict(width=1.2)))
    fig.add_trace(go.Scatter(x=dates, y=ema50, mode="lines", name="EMA 50",
                             line=dict(width=1.2)))
    fig.add_trace(go.Scatter(x=dates, y=bb_up, mode="lines", name="BB sup",
                             line=dict(width=0.8, dash="dot")))
    fig.add_trace(go.Scatter(x=dates, y=bb_lo, mode="lines", name="BB inf",
                             line=dict(width=0.8, dash="dot")))
    fig.update_layout(
        height=520,
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis_rangeslider_visible=False,
        template="plotly_white",
        legend=dict(orientation="h", y=1.05),
    )
    return to_html(fig, include_plotlyjs="cdn", full_html=False)


@app.route("/ticker/<symbol>")
def ticker_detail(symbol: str):
    symbol = symbol.upper()
    with session_scope() as session:
        ticker = session.scalar(select(Ticker).where(Ticker.symbol == symbol))
        if ticker is None:
            abort(404)

        prices = list(session.scalars(
            select(PriceDaily)
            .where(PriceDaily.ticker_id == ticker.id)
            .order_by(PriceDaily.trade_date)
        ).all())

        latest = prices[-1] if prices else None
        pred = _latest_prediction(session, ticker.id)

        cutoff = (latest.trade_date if latest else date.today()) - timedelta(days=14)
        news_rows = session.execute(
            select(NewsScored, NewsRaw)
            .join(NewsRaw, NewsRaw.id == NewsScored.news_id)
            .where(NewsScored.ticker_id == ticker.id)
            .where(NewsRaw.published >= cutoff)
            .order_by(desc(NewsRaw.published))
            .limit(20)
        ).all()
        news = [
            {
                "title": n.title,
                "link": n.link,
                "source": n.source,
                "published": n.published,
                "category": s.category,
                "sentiment": s.sentiment,
                "relevance": s.relevance,
            }
            for s, n in news_rows
        ]

    chart_html = _build_chart(prices[-120:] if prices else [])
    return render_template(
        "ticker.html",
        symbol=symbol,
        name=ticker.name or symbol,
        latest=latest,
        prediction=pred,
        news=news,
        chart_html=chart_html,
    )


@app.template_filter("brl")
def _brl(value):
    if value is None:
        return "—"
    return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


@app.template_filter("pct")
def _pct(value):
    if value is None:
        return "—"
    return f"{float(value):+.2f}%"


@app.template_filter("d")
def _d(value):
    if value is None:
        return "—"
    return value.strftime("%d/%m/%Y") if hasattr(value, "strftime") else str(value)


def _ensure_db():
    init_db()


if __name__ == "__main__":
    _ensure_db()
    app.run(host="127.0.0.1", port=5000, debug=True)
