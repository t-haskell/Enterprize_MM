"""Prefect flows orchestrating multi-source data ingestion."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List

import pandas as pd
from prefect import flow, task
from sqlalchemy import text

from .db import engine


@task
def fetch_ohlcv(symbol: str, days: int = 365) -> pd.DataFrame:
    """Fetch OHLCV data (synthetic placeholder)."""

    now = datetime.utcnow()
    data = [
        {
            "ts": now - timedelta(days=i),
            "open": 100 + i * 0.3,
            "high": 101 + i * 0.3,
            "low": 99 + i * 0.3,
            "close": 100 + i * 0.3,
            "volume": 1_000_000 + i * 10,
        }
        for i in range(days)
    ]
    df = pd.DataFrame(data)
    df.sort_values("ts", inplace=True)
    return df


@task
def write_prices(symbol: str, df: pd.DataFrame) -> None:
    with engine().begin() as conn:
        sid = conn.execute(
            text(
                """
                INSERT INTO symbols(symbol) VALUES(:symbol)
                ON CONFLICT(symbol) DO UPDATE SET symbol=EXCLUDED.symbol
                RETURNING id
                """
            ),
            {"symbol": symbol},
        ).scalar()
        df["symbol_id"] = sid
        df.to_sql("ohlcv", conn.connection, if_exists="append", index=False)


@task
def fetch_fundamentals(symbols: List[str]) -> pd.DataFrame:
    """Synthetic fundamentals placeholder returning margin/valuation metrics."""

    rows: List[Dict[str, float]] = []
    for symbol in symbols:
        rows.append(
            {
                "symbol": symbol,
                "gross_margin": 0.4,
                "net_margin": 0.18,
                "revenue_growth_1y": 0.12,
                "fcf_yield": 0.05,
                "updated_at": datetime.utcnow(),
            }
        )
    return pd.DataFrame(rows)


@task
def write_fundamentals(df: pd.DataFrame) -> None:
    with engine().begin() as conn:
        df.to_sql("fundamentals", conn.connection, if_exists="append", index=False)


@task
def fetch_macro_signals() -> pd.DataFrame:
    """Produce synthetic macro indicators for regime detection."""

    now = datetime.utcnow()
    data = [
        {"as_of": now, "indicator": "inflation_trend", "value": 0.02},
        {"as_of": now, "indicator": "gdp_trend", "value": 0.025},
        {"as_of": now, "indicator": "rates_trend", "value": 0.03},
    ]
    return pd.DataFrame(data)


@task
def write_macro(df: pd.DataFrame) -> None:
    with engine().begin() as conn:
        df.to_sql("macro_signals", conn.connection, if_exists="append", index=False)


@task
def fetch_sentiment(symbols: List[str]) -> pd.DataFrame:
    now = datetime.utcnow()
    rows = []
    for symbol in symbols:
        rows.append(
            {
                "symbol": symbol,
                "headline": f"Synthetic headline for {symbol}",
                "sentiment_score": 0.1,
                "source": "stub",
                "published_at": now,
            }
        )
    return pd.DataFrame(rows)


@task
def write_sentiment(df: pd.DataFrame) -> None:
    with engine().begin() as conn:
        df.to_sql("news_sentiment", conn.connection, if_exists="append", index=False)


@flow
def ingest_ohlcv(symbol: str = "AAPL") -> None:
    df = fetch_ohlcv(symbol)
    write_prices(symbol, df)


@flow
def ingest_fundamentals(symbols: List[str]) -> None:
    df = fetch_fundamentals(symbols)
    write_fundamentals(df)


@flow
def ingest_macro() -> None:
    df = fetch_macro_signals()
    write_macro(df)


@flow
def ingest_sentiment(symbols: List[str]) -> None:
    df = fetch_sentiment(symbols)
    write_sentiment(df)


@flow
def ingest_all(symbols: List[str]) -> None:
    for symbol in symbols:
        ingest_ohlcv(symbol)
    ingest_fundamentals(symbols)
    ingest_macro()
    ingest_sentiment(symbols)
