"""Lightweight embedding utilities for scenario ranking."""
from __future__ import annotations

import hashlib
import math
from typing import Iterable, List


class EmbeddingService:
    """Derive deterministic embeddings from text without external services.

    The service uses a simple hashed bag-of-words representation so tests can run
    without network connectivity or heavyweight ML dependencies. The hashed
    vectors are normalised, allowing cosine similarity comparisons between
    prompts and scenario templates.
    """

    def __init__(self, dimension: int = 128) -> None:
        self.dimension = dimension

    def embed_text(self, text: str) -> List[float]:
        tokens = self._tokenize(text)
        vector = [0.0] * self.dimension
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimension
            vector[bucket] += 1.0
        return self._normalise(vector)

    def embed_keywords(self, keywords: Iterable[str]) -> List[float]:
        return self.embed_text(" ".join(sorted(set(keywords))))

    def embed_prompt(self, prompt: str) -> List[float]:
        return self.embed_text(prompt)

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return [token.lower() for token in text.split() if token]

    @staticmethod
    def _normalise(vector: List[float]) -> List[float]:
        norm = math.sqrt(sum(value * value for value in vector))
        if not norm:
            return vector
        return [value / norm for value in vector]


_EMBEDDINGS = EmbeddingService()


def get_embedder() -> EmbeddingService:
    return _EMBEDDINGS
