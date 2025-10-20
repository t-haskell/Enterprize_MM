"""Prompt-to-scenario ranking logic."""
from __future__ import annotations

import math
from collections import Counter
from typing import Iterable, List

from .catalog import SCENARIO_CATALOG, scenario_specs
from .embeddings import get_embedder
from .models import PromptRequest, ScenarioOption, ScenarioSpec, ScenarioSuggestionResponse

_EMBEDDER = get_embedder()


def _tokenize(text: str) -> List[str]:
    return [token.lower() for token in text.split() if token]


def _keyword_score(prompt_tokens: Counter, keywords: Iterable[str]) -> float:
    score = 0.0
    for keyword in keywords:
        frequency = prompt_tokens.get(keyword.lower(), 0)
        if frequency:
            score += 1.4 * frequency
        elif any(keyword.lower() in token for token in prompt_tokens):
            score += 0.6
    score += math.log1p(sum(prompt_tokens.values())) * 0.05
    return score


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(i * j for i, j in zip(a, b))
    norm_a = math.sqrt(sum(i * i for i in a))
    norm_b = math.sqrt(sum(i * i for i in b))
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)


def _temperature_scale(score: float, temperature: float) -> float:
    temperature = min(max(temperature, 0.1), 2.0)
    return score ** (1.0 / temperature)


def _eligible(spec: ScenarioSpec, user_profile: dict | None) -> bool:
    if not user_profile:
        return True
    jurisdiction = user_profile.get("jurisdiction")
    if jurisdiction and jurisdiction in spec.restricted_regions:
        return False
    excluded_tags = set(user_profile.get("excluded_tags", []))
    if excluded_tags.intersection(spec.tags) or excluded_tags.intersection(spec.eligibility_tags):
        return False
    if spec.requires_accreditation and not user_profile.get("accredited_investor", False):
        return False
    regulatory_flags = set(user_profile.get("regulatory_flags", []))
    if regulatory_flags.intersection(spec.eligibility_tags):
        return False
    return True


def rank_scenarios(request: PromptRequest) -> ScenarioSuggestionResponse:
    tokens = Counter(_tokenize(request.prompt))
    prompt_embedding = _EMBEDDER.embed_prompt(request.prompt)
    options: List[ScenarioOption] = []

    temperature = 0.7
    if request.user_profile and isinstance(request.user_profile.get("temperature"), (int, float)):
        temperature = float(request.user_profile["temperature"])

    for spec in scenario_specs():
        if not _eligible(spec, request.user_profile):
            continue
        similarity = _cosine_similarity(prompt_embedding, spec.embedding)
        keyword_boost = _keyword_score(tokens, spec.keywords)
        if request.user_profile:
            risk_profile = request.user_profile.get("risk_profile")
            if risk_profile == "conservative" and ("volatility" in spec.keywords or "hedging" in spec.tags):
                keyword_boost *= 0.75
            if risk_profile == "aggressive" and "momentum" in spec.tags:
                keyword_boost *= 1.1
        raw_score = max(similarity, 0.0) + keyword_boost
        final_score = _temperature_scale(max(raw_score, 1e-6), temperature)

        options.append(
            ScenarioOption(
                scenario_id=spec.scenario_id,
                title=spec.title,
                short_description=spec.short_description,
                rationale=spec.rationale,
                inputs=spec.inputs,
                methodology=spec.methodology,
                deliverables=spec.deliverables,
                score=round(final_score, 4),
            )
        )

    options.sort(key=lambda opt: opt.score, reverse=True)
    max_items = request.max_scenarios
    trimmed = [opt for opt in options if opt.score > 0][:max_items]
    if not trimmed:
        trimmed = options[:max_items]
    metadata = {
        "scored": len(trimmed),
        "total_available": len(SCENARIO_CATALOG),
        "temperature": temperature,
    }
    return ScenarioSuggestionResponse(prompt=request.prompt, options=trimmed, metadata=metadata)
