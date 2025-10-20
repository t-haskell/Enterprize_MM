from __future__ import annotations

import importlib
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import pytest
from sqlalchemy import text

from ingestion.flows import (
    transform_equity_prices,
    transform_fundamentals,
    transform_insider_activity,
    transform_macro_signals,
    transform_news_sentiment,
)


def test_transform_equity_prices_schema():
    raw = pd.DataFrame(
        {
            "symbol": ["AAPL", "AAPL", "AAPL"],
            "ts": pd.date_range("2023-01-01", periods=3, freq="D"),
            "open": [100, 101, 102],
            "high": [101, 102, 103],
            "low": [99, 100, 101],
            "close": [100, 102, 101],
            "volume": [1_000_000, 1_100_000, 1_050_000],
        }
    )
    curated = transform_equity_prices.fn(raw)
    assert set(curated.columns) == {"symbol", "ts", "close", "return_1d", "volume_ma_5", "volatility_5d"}
    assert len(curated) == 2
    assert pytest.approx(curated.iloc[0]["return_1d"], rel=1e-3) == 0.02


def test_transform_fundamentals_schema():
    raw = pd.DataFrame(
        {
            "symbol": ["AAPL", "AAPL"],
            "cik": ["0000000001", "0000000001"],
            "metric": ["revenue", "revenue"],
            "value": [1000.0, 1100.0],
            "period_end": ["2023-03-31", "2023-06-30"],
        }
    )
    curated = transform_fundamentals.fn(raw)
    assert set(curated.columns) == {
        "symbol",
        "as_of",
        "revenue",
        "revenue_growth",
        "margin_score",
        "quality_rank",
    }
    assert len(curated) == 1
    assert pytest.approx(curated.iloc[0]["revenue_growth"], rel=1e-3) == 0.1


def test_transform_news_sentiment_schema():
    now = datetime.utcnow()
    raw = pd.DataFrame(
        {
            "symbol": ["AAPL", "AAPL", "MSFT"],
            "headline": ["a", "b", "c"],
            "relevance": [0.5, 0.6, 0.7],
            "sentiment": [0.1, 0.2, -0.3],
            "event_time": [now.isoformat()] * 3,
        }
    )
    curated = transform_news_sentiment.fn(raw)
    assert set(curated.columns) == {"symbol", "avg_sentiment", "article_count", "avg_relevance", "as_of"}
    row = curated.loc[curated["symbol"] == "AAPL"].iloc[0]
    assert pytest.approx(row["avg_sentiment"], rel=1e-6) == 0.15
    assert row["article_count"] == 2


def test_transform_macro_signals_schema():
    now = datetime.utcnow()
    raw = pd.DataFrame(
        [
            {"indicator": "inflation", "value": 2.5, "as_of": now},
            {"indicator": "gdp_growth", "value": 2.4, "as_of": now},
            {"indicator": "rates", "value": 3.0, "as_of": now},
        ]
    )
    curated = transform_macro_signals.fn(raw)
    assert "regime" in curated.columns
    assert curated.iloc[0]["regime"] == "expansion"


def test_transform_insider_activity_schema():
    raw = pd.DataFrame(
        {
            "symbol": ["AAPL", "AAPL", "MSFT"],
            "insider": ["John", "Jane", "Terry"],
            "role": ["CEO", "CFO", "Director"],
            "transaction_type": ["Buy", "Sell", "Buy"],
            "shares": [1000, 200, 300],
            "transaction_date": ["2023-01-01", "2023-01-05", "2023-01-03"],
            "price": [150.0, 152.0, 250.0],
            "source": ["synthetic"] * 3,
        }
    )
    curated = transform_insider_activity.fn(raw)
    assert set(curated.columns) == {"symbol", "buy_shares", "sell_shares", "net_shares", "as_of"}
    apple = curated.loc[curated["symbol"] == "AAPL"].iloc[0]
    assert apple["net_shares"] == pytest.approx(800)


def test_record_data_freshness_upsert(tmp_path, monkeypatch):
    db_path = tmp_path / "ingestion.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    db_module = importlib.import_module("ingestion.db")
    importlib.reload(db_module)

    with db_module.db_session() as conn:
        db_module.record_data_freshness(
            conn,
            dataset="equities",
            last_updated=datetime.utcnow() - timedelta(days=1),
            row_count=10,
        )
        result = conn.execute(text("SELECT row_count FROM data_freshness WHERE dataset='equities'"))
        assert result.scalar_one() == 10

    with db_module.db_session() as conn:
        db_module.record_data_freshness(
            conn,
            dataset="equities",
            last_updated=datetime.utcnow(),
            row_count=25,
        )
        result = conn.execute(text("SELECT row_count FROM data_freshness WHERE dataset='equities'"))
        assert result.scalar_one() == 25
