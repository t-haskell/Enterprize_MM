"""Persistence utilities for orchestration run metadata."""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    import redis  # type: ignore
except Exception:  # pragma: no cover - executed when redis isn't available
    redis = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import psycopg  # type: ignore
except Exception:  # pragma: no cover - executed when psycopg isn't available
    psycopg = None  # type: ignore


@dataclass
class RunStore:
    """Persist orchestration run metadata to Redis and/or Postgres."""

    redis_url: Optional[str] = None
    postgres_url: Optional[str] = None
    namespace: str = "orchestration:run"
    _memory: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    _redis: Any = field(init=False, default=None)
    _pg_conn: Any = field(init=False, default=None)

    def __post_init__(self) -> None:
        self.redis_url = self.redis_url or os.getenv("REDIS_URL")
        self.postgres_url = self.postgres_url or os.getenv("ORCHESTRATION_DATABASE_URL") or os.getenv("DATABASE_URL")
        if self.redis_url and redis:
            try:
                self._redis = redis.Redis.from_url(self.redis_url, decode_responses=True)
                self._redis.ping()
            except Exception as exc:  # pragma: no cover - runtime logging
                logger.warning("Redis unavailable: %s", exc)
                self._redis = None
        if self.postgres_url and psycopg:
            try:
                self._pg_conn = psycopg.connect(self.postgres_url, autocommit=True)
                with self._pg_conn.cursor() as cur:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS orchestration_runs (
                            run_id TEXT PRIMARY KEY,
                            payload JSONB NOT NULL
                        )
                        """
                    )
            except Exception as exc:  # pragma: no cover - runtime logging
                logger.warning("Postgres unavailable: %s", exc)
                self._pg_conn = None

    def _redis_key(self, run_id: str) -> str:
        return f"{self.namespace}:{run_id}"

    def create(self, run_id: str, payload: Dict[str, Any]) -> None:
        self._memory[run_id] = payload
        self._persist(run_id, payload)

    def update(self, run_id: str, payload: Dict[str, Any]) -> None:
        self._memory[run_id] = payload
        self._persist(run_id, payload)

    def get(self, run_id: str) -> Optional[Dict[str, Any]]:
        if run_id in self._memory:
            return self._memory[run_id]
        data = self._read(run_id)
        if data is not None:
            self._memory[run_id] = data
        return data

    def _persist(self, run_id: str, payload: Dict[str, Any]) -> None:
        serialized = json.dumps(payload)
        if self._redis:
            try:
                self._redis.set(self._redis_key(run_id), serialized)
            except Exception as exc:  # pragma: no cover - runtime logging
                logger.warning("Failed to persist run %s to Redis: %s", run_id, exc)
        if self._pg_conn:
            try:
                with self._pg_conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO orchestration_runs (run_id, payload)
                        VALUES (%s, %s)
                        ON CONFLICT (run_id) DO UPDATE SET payload = EXCLUDED.payload
                        """,
                        (run_id, serialized),
                    )
            except Exception as exc:  # pragma: no cover - runtime logging
                logger.warning("Failed to persist run %s to Postgres: %s", run_id, exc)

    def _read(self, run_id: str) -> Optional[Dict[str, Any]]:
        if self._redis:
            try:
                raw = self._redis.get(self._redis_key(run_id))
                if raw:
                    return json.loads(raw)
            except Exception as exc:  # pragma: no cover - runtime logging
                logger.warning("Failed to read run %s from Redis: %s", run_id, exc)
        if self._pg_conn:
            try:
                with self._pg_conn.cursor() as cur:
                    cur.execute("SELECT payload FROM orchestration_runs WHERE run_id = %s", (run_id,))
                    row = cur.fetchone()
                if row and row[0]:
                    return json.loads(row[0])
            except Exception as exc:  # pragma: no cover - runtime logging
                logger.warning("Failed to read run %s from Postgres: %s", run_id, exc)
        return None


_STORE = RunStore()


def get_run_store() -> RunStore:
    return _STORE
