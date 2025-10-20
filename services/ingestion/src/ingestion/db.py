"""Database helpers for ingestion flows."""
from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime
from typing import Iterable, Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine

_ENGINE: Optional[Engine] = None


def get_engine() -> Engine:
    """Return a shared SQLAlchemy engine configured from ``DATABASE_URL``."""

    global _ENGINE
    if _ENGINE is None:
        url = os.getenv("DATABASE_URL")
        if not url:
            raise RuntimeError("DATABASE_URL not set")
        _ENGINE = create_engine(url, pool_pre_ping=True, future=True)
    return _ENGINE


@contextmanager
def db_session() -> Iterable[Connection]:
    """Yield a transactional SQLAlchemy connection."""

    engine = get_engine()
    with engine.begin() as conn:
        yield conn


def write_dataframe(
    conn: Connection,
    df: pd.DataFrame,
    table: str,
    *,
    schema: Optional[str] = None,
    if_exists: str = "append",
) -> None:
    """Write a dataframe to the provided connection with consistent options."""

    if df.empty:
        return
    df.to_sql(
        table,
        conn.connection,
        schema=schema,
        if_exists=if_exists,
        index=False,
        method="multi",
    )


def ensure_freshness_table(conn: Connection) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS data_freshness (
                dataset TEXT PRIMARY KEY,
                last_updated TIMESTAMP NOT NULL,
                row_count INTEGER NOT NULL,
                status TEXT NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
            """
        )
    )


def record_data_freshness(
    conn: Connection,
    *,
    dataset: str,
    last_updated: datetime,
    row_count: int,
    status: str = "success",
) -> None:
    """Upsert orchestration metadata for a dataset."""

    ensure_freshness_table(conn)
    conn.execute(
        text(
            """
            INSERT INTO data_freshness(dataset, last_updated, row_count, status, updated_at)
            VALUES(:dataset, :last_updated, :row_count, :status, :updated_at)
            ON CONFLICT(dataset) DO UPDATE SET
                last_updated = EXCLUDED.last_updated,
                row_count = EXCLUDED.row_count,
                status = EXCLUDED.status,
                updated_at = EXCLUDED.updated_at
            """
        ),
        {
            "dataset": dataset,
            "last_updated": last_updated,
            "row_count": row_count,
            "status": status,
            "updated_at": datetime.utcnow(),
        },
    )
