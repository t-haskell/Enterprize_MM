"""Prefect flows orchestrating multi-source data ingestion."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, List, Optional

import pandas as pd
from prefect import flow, get_run_logger, task

from .db import db_session, record_data_freshness, write_dataframe
from .vendors import (
    InsiderActivityClient,
    MacroSignalsClient,
    PolygonClient,
    RavenPackClient,
    SECEdgarClient,
)

DEFAULT_EQUITY_LOOKBACK_DAYS = 365


def _window(days: int) -> tuple[datetime, datetime]:
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    return start, end


def _persist_dataset(
    dataset: str,
    raw_df: pd.DataFrame,
    curated_df: pd.DataFrame,
    *,
    raw_table: str,
    curated_table: str,
    curated_schema: Optional[str] = None,
) -> None:
    with db_session() as conn:
        if not raw_df.empty:
            write_dataframe(conn, raw_df, raw_table)
        if not curated_df.empty:
            write_dataframe(conn, curated_df, curated_table, schema=curated_schema)
        as_of_value = datetime.utcnow()
        for candidate in ("as_of", "ts", "timestamp"):
            if candidate in curated_df.columns and not curated_df.empty:
                as_of_value = pd.to_datetime(curated_df[candidate]).max()
                break
        record_data_freshness(
            conn,
            dataset=dataset,
            last_updated=as_of_value,
            row_count=int(curated_df.shape[0]),
        )


@task(name="fetch_equity_prices")
def fetch_equity_prices(
    symbols: Iterable[str],
    *,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> pd.DataFrame:
    logger = get_run_logger()
    if start is None or end is None:
        start, end = _window(DEFAULT_EQUITY_LOOKBACK_DAYS)
    client = PolygonClient.from_env()
    frames: List[pd.DataFrame] = []
    for symbol in symbols:
        frame = client.get_aggregates(symbol, start, end)
        if frame.empty:
            logger.warning("No equity bars returned for symbol %s", symbol)
            continue
        frames.append(frame)
    if not frames:
        return pd.DataFrame(columns=["symbol", "ts", "open", "high", "low", "close", "volume"])
    combined = pd.concat(frames, ignore_index=True)
    combined.sort_values(["symbol", "ts"], inplace=True)
    return combined


@task(name="transform_equity_prices")
def transform_equity_prices(raw_df: pd.DataFrame) -> pd.DataFrame:
    if raw_df.empty:
        return raw_df
    curated = raw_df.copy()
    curated["return_1d"] = curated.groupby("symbol")["close"].pct_change()
    curated["volume_ma_5"] = (
        curated.groupby("symbol")["volume"].transform(lambda s: s.rolling(window=5, min_periods=1).mean())
    )
    curated["volatility_5d"] = (
        curated.groupby("symbol")["return_1d"].transform(lambda s: s.rolling(window=5, min_periods=1).std())
    )
    curated.dropna(subset=["return_1d"], inplace=True)
    curated.rename(columns={"ts": "ts"}, inplace=True)
    curated = curated[[
        "symbol",
        "ts",
        "close",
        "return_1d",
        "volume_ma_5",
        "volatility_5d",
    ]]
    curated["ts"] = pd.to_datetime(curated["ts"])
    return curated


@task(name="load_equity_prices")
def load_equity_prices(raw_df: pd.DataFrame, curated_df: pd.DataFrame) -> None:
    _persist_dataset(
        "equities",
        raw_df,
        curated_df,
        raw_table="raw_equity_ohlcv",
        curated_table="equity_price_factors",
        curated_schema="factor_inputs",
    )


@flow(name="equities_ingestion")
def equities_ingestion_flow(symbols: Iterable[str], days: int = DEFAULT_EQUITY_LOOKBACK_DAYS) -> None:
    start, end = _window(days)
    raw = fetch_equity_prices(symbols, start=start, end=end)
    curated = transform_equity_prices(raw)
    load_equity_prices(raw, curated)


def _enumerate_ciks(symbols: Iterable[str]) -> List[tuple[str, str]]:
    return [(symbol, f"{idx+1:010d}") for idx, symbol in enumerate(symbols)]


@task(name="fetch_fundamental_filings")
def fetch_fundamental_filings(symbols: Iterable[str]) -> pd.DataFrame:
    client = SECEdgarClient.from_env()
    rows: List[dict] = []
    for symbol, cik in _enumerate_ciks(symbols):
        facts = client.get_company_facts(cik)
        taxonomy = facts.get("facts", {})
        revenues: List[dict] = []

        for key in ("us-gaap", "IncomeStatement"):
            container = taxonomy.get(key, {})
            revenue_fact = container.get("Revenues", {}) if isinstance(container, dict) else {}
            revenues = revenue_fact.get("units", {}).get("USD", [])
            if revenues:
                break

        if not revenues:
            for container in taxonomy.values():
                if not isinstance(container, dict):
                    continue
                revenue_fact = container.get("Revenues", {})
                if not isinstance(revenue_fact, dict):
                    continue
                revenues = revenue_fact.get("units", {}).get("USD", [])
                if revenues:
                    break

        for entry in revenues:
            rows.append(
                {
                    "symbol": symbol,
                    "cik": cik,
                    "metric": "revenue",
                    "value": entry.get("val"),
                    "period_end": entry.get("end"),
                }
            )
    return pd.DataFrame(rows)


@task(name="transform_fundamentals")
def transform_fundamentals(raw_df: pd.DataFrame) -> pd.DataFrame:
    if raw_df.empty:
        return raw_df
    df = raw_df.copy()
    df["period_end"] = pd.to_datetime(df["period_end"])
    df.sort_values(["symbol", "period_end"], inplace=True)
    df["revenue_growth"] = df.groupby("symbol")["value"].pct_change()
    df["margin_score"] = df["revenue_growth"].fillna(0).clip(-1, 1)
    df["quality_rank"] = df.groupby("period_end")["value"].rank(ascending=False)
    curated = df.dropna(subset=["revenue_growth"])
    curated = curated[["symbol", "period_end", "value", "revenue_growth", "margin_score", "quality_rank"]]
    curated.rename(columns={"period_end": "as_of", "value": "revenue"}, inplace=True)
    return curated


@task(name="load_fundamentals")
def load_fundamentals(raw_df: pd.DataFrame, curated_df: pd.DataFrame) -> None:
    _persist_dataset(
        "fundamentals",
        raw_df,
        curated_df,
        raw_table="raw_fundamentals",
        curated_table="fundamental_quality",
        curated_schema="factor_inputs",
    )


@flow(name="fundamentals_ingestion")
def fundamentals_ingestion_flow(symbols: Iterable[str]) -> None:
    raw = fetch_fundamental_filings(symbols)
    curated = transform_fundamentals(raw)
    load_fundamentals(raw, curated)


@task(name="fetch_news_sentiment")
def fetch_news_sentiment(symbols: Iterable[str]) -> pd.DataFrame:
    client = RavenPackClient.from_env()
    return client.get_news(symbols)


@task(name="transform_news_sentiment")
def transform_news_sentiment(raw_df: pd.DataFrame) -> pd.DataFrame:
    if raw_df.empty:
        return raw_df
    df = raw_df.copy()
    df["event_time"] = pd.to_datetime(df["event_time"])
    aggregated = (
        df.groupby("symbol")
        .agg(
            avg_sentiment=("sentiment", "mean"),
            article_count=("headline", "count"),
            avg_relevance=("relevance", "mean"),
        )
        .reset_index()
    )
    aggregated["as_of"] = df["event_time"].max()
    columns = ["symbol", "avg_sentiment", "article_count", "avg_relevance", "as_of"]
    return aggregated[columns]


@task(name="load_news_sentiment")
def load_news_sentiment(raw_df: pd.DataFrame, curated_df: pd.DataFrame) -> None:
    _persist_dataset(
        "news_nlp",
        raw_df,
        curated_df,
        raw_table="raw_news_sentiment",
        curated_table="news_sentiment_signals",
        curated_schema="earnings_events",
    )


@flow(name="news_ingestion")
def news_nlp_ingestion_flow(symbols: Iterable[str]) -> None:
    raw = fetch_news_sentiment(symbols)
    curated = transform_news_sentiment(raw)
    load_news_sentiment(raw, curated)


@task(name="fetch_macro_signals")
def fetch_macro_signals() -> pd.DataFrame:
    client = MacroSignalsClient.from_env()
    return client.latest_signals()


@task(name="transform_macro_signals")
def transform_macro_signals(raw_df: pd.DataFrame) -> pd.DataFrame:
    if raw_df.empty:
        return raw_df
    df = raw_df.copy()
    df["as_of"] = pd.to_datetime(df["as_of"])
    pivot = df.pivot_table(index="as_of", columns="indicator", values="value")
    pivot.reset_index(inplace=True)
    pivot["regime"] = pivot.apply(
        lambda row: "expansion" if row.get("gdp_growth", 0) > 2 and row.get("inflation", 0) < 3 else "slowdown",
        axis=1,
    )
    return pivot


@task(name="load_macro_signals")
def load_macro_signals(raw_df: pd.DataFrame, curated_df: pd.DataFrame) -> None:
    _persist_dataset(
        "macro_signals",
        raw_df,
        curated_df,
        raw_table="raw_macro_signals",
        curated_table="macro_regime_signals",
        curated_schema="macro_regimes",
    )


@flow(name="macro_ingestion")
def macro_signals_ingestion_flow() -> None:
    raw = fetch_macro_signals()
    curated = transform_macro_signals(raw)
    load_macro_signals(raw, curated)


@task(name="fetch_insider_activity")
def fetch_insider_activity(symbols: Iterable[str]) -> pd.DataFrame:
    client = InsiderActivityClient.from_env()
    return client.latest_activity(symbols)


@task(name="transform_insider_activity")
def transform_insider_activity(raw_df: pd.DataFrame) -> pd.DataFrame:
    if raw_df.empty:
        return raw_df
    df = raw_df.copy()
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    grouped = (
        df.groupby(["symbol", "transaction_type"])
        .agg(
            total_shares=("shares", "sum"),
            avg_price=("price", "mean"),
            last_transaction=("transaction_date", "max"),
        )
        .reset_index()
    )
    pivot = grouped.pivot(index="symbol", columns="transaction_type", values="total_shares").fillna(0)
    pivot.reset_index(inplace=True)
    pivot.rename(columns={"Buy": "buy_shares", "Sell": "sell_shares"}, inplace=True)
    buy_series = pivot["buy_shares"] if "buy_shares" in pivot.columns else pd.Series(0, index=pivot.index)
    sell_series = pivot["sell_shares"] if "sell_shares" in pivot.columns else pd.Series(0, index=pivot.index)
    pivot["net_shares"] = buy_series - sell_series
    pivot["as_of"] = grouped["last_transaction"].max()
    if "buy_shares" not in pivot:
        pivot["buy_shares"] = 0
    if "sell_shares" not in pivot:
        pivot["sell_shares"] = 0
    columns = ["symbol", "buy_shares", "sell_shares", "net_shares", "as_of"]
    return pivot[columns]


@task(name="load_insider_activity")
def load_insider_activity(raw_df: pd.DataFrame, curated_df: pd.DataFrame) -> None:
    _persist_dataset(
        "insider_buyback",
        raw_df,
        curated_df,
        raw_table="raw_insider_activity",
        curated_table="insider_buyback_activity",
        curated_schema="earnings_events",
    )


@flow(name="insider_ingestion")
def insider_buyback_ingestion_flow(symbols: Iterable[str]) -> None:
    raw = fetch_insider_activity(symbols)
    curated = transform_insider_activity(raw)
    load_insider_activity(raw, curated)


@flow(name="enterprise_multi_source_ingestion")
def enterprise_ingestion_flow(symbols: Iterable[str]) -> None:
    equities_ingestion_flow(symbols)
    fundamentals_ingestion_flow(symbols)
    news_nlp_ingestion_flow(symbols)
    macro_signals_ingestion_flow()
    insider_buyback_ingestion_flow(symbols)
