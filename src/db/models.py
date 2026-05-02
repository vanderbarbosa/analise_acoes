"""Schema SQLAlchemy + bootstrap do SQLite."""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)

from config import DATABASE_URL, DATA_DIR


class Base(DeclarativeBase):
    pass


class Ticker(Base):
    __tablename__ = "tickers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    yahoo_symbol: Mapped[str] = mapped_column(String(24), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(128))

    prices: Mapped[list["PriceDaily"]] = relationship(back_populates="ticker", cascade="all, delete-orphan")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="ticker", cascade="all, delete-orphan")


class PriceDaily(Base):
    __tablename__ = "price_daily"
    __table_args__ = (UniqueConstraint("ticker_id", "trade_date", name="uq_price_ticker_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker_id: Mapped[int] = mapped_column(ForeignKey("tickers.id"), nullable=False, index=True)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    rsi: Mapped[Optional[float]] = mapped_column(Float)
    macd: Mapped[Optional[float]] = mapped_column(Float)
    macd_signal: Mapped[Optional[float]] = mapped_column(Float)
    macd_hist: Mapped[Optional[float]] = mapped_column(Float)
    ema_9: Mapped[Optional[float]] = mapped_column(Float)
    ema_21: Mapped[Optional[float]] = mapped_column(Float)
    ema_50: Mapped[Optional[float]] = mapped_column(Float)
    bb_upper: Mapped[Optional[float]] = mapped_column(Float)
    bb_lower: Mapped[Optional[float]] = mapped_column(Float)
    bb_mid: Mapped[Optional[float]] = mapped_column(Float)
    atr: Mapped[Optional[float]] = mapped_column(Float)
    tech_score: Mapped[Optional[float]] = mapped_column(Float)

    ticker: Mapped["Ticker"] = relationship(back_populates="prices")


class NewsRaw(Base):
    __tablename__ = "news_raw"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    link: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    published: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    scores: Mapped[list["NewsScored"]] = relationship(back_populates="news", cascade="all, delete-orphan")


class NewsScored(Base):
    __tablename__ = "news_scored"
    __table_args__ = (UniqueConstraint("news_id", "ticker_id", name="uq_newsscore_news_ticker"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    news_id: Mapped[int] = mapped_column(ForeignKey("news_raw.id"), nullable=False, index=True)
    ticker_id: Mapped[int] = mapped_column(ForeignKey("tickers.id"), nullable=False, index=True)

    category: Mapped[str] = mapped_column(String(32), nullable=False)
    relevance: Mapped[float] = mapped_column(Float, nullable=False)
    sentiment: Mapped[float] = mapped_column(Float, nullable=False)
    impact: Mapped[float] = mapped_column(Float, nullable=False)

    news: Mapped["NewsRaw"] = relationship(back_populates="scores")


class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = (UniqueConstraint("ticker_id", "for_date", name="uq_pred_ticker_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker_id: Mapped[int] = mapped_column(ForeignKey("tickers.id"), nullable=False, index=True)
    for_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    direction: Mapped[str] = mapped_column(String(8), nullable=False)
    magnitude_pct: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    news_score: Mapped[float] = mapped_column(Float, nullable=False)
    tech_score: Mapped[float] = mapped_column(Float, nullable=False)
    combined_score: Mapped[float] = mapped_column(Float, nullable=False)

    rationale: Mapped[Optional[str]] = mapped_column(Text)

    ticker: Mapped["Ticker"] = relationship(back_populates="predictions")


_engine = None
_SessionLocal: Optional[sessionmaker[Session]] = None


def get_engine():
    global _engine
    if _engine is None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(DATABASE_URL, echo=False, future=True)
    return _engine


def get_sessionmaker() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), expire_on_commit=False, future=True)
    return _SessionLocal


def session_scope() -> Session:
    return get_sessionmaker()()


def init_db() -> None:
    """Cria todas as tabelas e popula a tabela de tickers a partir do config."""
    from config import TICKERS

    engine = get_engine()
    Base.metadata.create_all(engine)

    with session_scope() as session:
        for symbol, yahoo_symbol in TICKERS.items():
            existing = session.query(Ticker).filter_by(symbol=symbol).one_or_none()
            if existing is None:
                session.add(Ticker(symbol=symbol, yahoo_symbol=yahoo_symbol, name=symbol))
        session.commit()
    print(f"[init_db] schema pronto em {DATABASE_URL}")
