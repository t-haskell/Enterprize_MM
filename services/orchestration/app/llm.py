"""Abstractions for interacting with the underlying language model provider."""
from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any, Dict, Protocol

from tenacity import RetryError, retry, stop_after_attempt, wait_exponential


class LLMProvider(Protocol):
    """Protocol describing the interface each provider should implement."""

    def complete(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:  # pragma: no cover - interface
        ...


@dataclass
class StubProvider:
    """Deterministic provider used for tests and local development."""

    name: str = "stub"

    def complete(self, prompt: str, **_: Any) -> Dict[str, Any]:
        word_count = len(prompt.split())
        return {
            "provider": self.name,
            "prompt_length": word_count,
            "echo": prompt[:120],
            "notes": "LLM stub executed; integrate provider SDK for production",
        }


class TokenBudgetExceeded(RuntimeError):
    """Raised when the prompt would exceed the configured token budget."""


class PromptEngine:
    """Wrapper around an LLM provider with retry/backoff and token budgeting."""

    def __init__(
        self,
        provider: LLMProvider | None = None,
        token_budget: int = 4096,
        max_attempts: int = 3,
    ) -> None:
        self._provider = provider or StubProvider()
        self._token_budget = token_budget
        self._default_attempts = max_attempts
        self._lock = threading.Lock()

    def reset_budget(self, value: int | None = None) -> None:
        with self._lock:
            self._token_budget = value if value is not None else 4096

    def remaining_budget(self) -> int:
        with self._lock:
            return self._token_budget

    def _estimate_tokens(self, prompt: str) -> int:
        return max(1, len(prompt.split()))

    def _consume_budget(self, tokens: int) -> None:
        with self._lock:
            if tokens > self._token_budget:
                raise TokenBudgetExceeded("Prompt exceeds remaining token budget")
            self._token_budget -= tokens

    def _refund_budget(self, tokens: int) -> None:
        with self._lock:
            self._token_budget += tokens

    def complete(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        tokens = self._estimate_tokens(prompt)
        self._consume_budget(tokens)
        try:
            attempts = kwargs.pop("max_attempts", 0) or self._default_attempts
            @retry(
                stop=stop_after_attempt(attempts),
                wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
                reraise=True,
            )
            def _call() -> Dict[str, Any]:
                return self._provider.complete(prompt, **kwargs)

            response = _call()
        except RetryError as exc:  # pragma: no cover - defensive branch
            self._refund_budget(tokens)
            raise exc.last_attempt.exception() if exc.last_attempt else exc
        except Exception:
            self._refund_budget(tokens)
            raise
        response.setdefault("token_usage", {})
        response["token_usage"].update({"prompt_tokens": tokens, "remaining_budget": self.remaining_budget()})
        return response
