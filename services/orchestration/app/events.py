"""Event emission utilities for orchestration progress updates."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    from aiokafka import AIOKafkaProducer  # type: ignore
except Exception:  # pragma: no cover - executed when aiokafka isn't installed
    AIOKafkaProducer = None  # type: ignore


@dataclass
class EventEmitter:
    """Emit orchestration lifecycle events to Kafka and in-process listeners."""

    topic: str = "orchestration.runs"
    kafka_bootstrap_servers: Optional[str] = None
    _producer: Any = field(init=False, default=None)
    _queues: Set[asyncio.Queue[str]] = field(default_factory=set)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def _ensure_producer(self) -> None:
        if not self.kafka_bootstrap_servers:
            self.kafka_bootstrap_servers = os.getenv("KAFKA_BROKER")
        if not self.kafka_bootstrap_servers or not AIOKafkaProducer:
            return
        if self._producer:
            return
        async with self._lock:
            if self._producer:
                return
            try:
                producer = AIOKafkaProducer(bootstrap_servers=self.kafka_bootstrap_servers)
                await producer.start()
                self._producer = producer
            except Exception as exc:  # pragma: no cover - runtime logging
                logger.warning("Kafka producer unavailable: %s", exc)
                self._producer = None

    async def emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        message = json.dumps({
            "event": event_type,
            "payload": payload,
            "ts": time.time(),
        })
        await self._emit_kafka(message)
        await self._emit_local(message)

    async def _emit_kafka(self, message: str) -> None:
        if not self.kafka_bootstrap_servers or not AIOKafkaProducer:
            return
        await self._ensure_producer()
        if not self._producer:
            return
        try:
            await self._producer.send_and_wait(self.topic, message.encode("utf-8"))
        except Exception as exc:  # pragma: no cover - runtime logging
            logger.warning("Failed to publish orchestration event: %s", exc)

    async def _emit_local(self, message: str) -> None:
        for queue in list(self._queues):
            try:
                await queue.put(message)
            except RuntimeError:  # pragma: no cover - queue is closed
                self._queues.discard(queue)

    def register_queue(self, queue: asyncio.Queue[str]) -> None:
        self._queues.add(queue)

    async def shutdown(self) -> None:
        if self._producer:
            try:
                await self._producer.stop()
            except Exception as exc:  # pragma: no cover - runtime logging
                logger.warning("Error closing Kafka producer: %s", exc)
        self._producer = None


_EMITTER = EventEmitter()


def get_event_emitter() -> EventEmitter:
    return _EMITTER
