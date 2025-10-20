"""Abstractions for interacting with the underlying language model provider."""
from __future__ import annotations

from typing import Any, Dict


class PromptEngine:
    """Thin wrapper around the LLM provider.

    In production this would wrap OpenAI, Azure OpenAI, or a self-hosted model
    with retries, structured prompting, and observability. For now we provide a
    deterministic stub so the orchestration pipeline can be exercised end to end.
    """

    def __init__(self, provider: str = "stub") -> None:
        self.provider = provider

    def complete(self, prompt: str, **_: Any) -> Dict[str, Any]:
        """Return deterministic metadata derived from the prompt.

        The orchestration service currently relies on deterministic ranking via
        keyword similarity, so the LLM is not yet queried. The stub is preserved
        to make the transition to a real LLM drop-in.
        """

        return {
            "provider": self.provider,
            "prompt_length": len(prompt.split()),
            "notes": "LLM stub executed; integrate provider SDK for production",
        }
