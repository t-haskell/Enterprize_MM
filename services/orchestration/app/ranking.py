"""Prompt-to-scenario ranking logic."""
from __future__ import annotations

import math
from collections import Counter
from typing import Iterable, List

from .catalog import SCENARIO_CATALOG
from .models import PromptRequest, ScenarioOption, ScenarioSuggestionResponse


def _tokenize(text: str) -> List[str]:
    return [token.lower() for token in text.split() if token.isalpha() or token.isalnum()]


def _score(prompt_tokens: Counter, keywords: Iterable[str]) -> float:
    score = 0.0
    for keyword in keywords:
        frequency = prompt_tokens.get(keyword.lower(), 0)
        if frequency:
            score += 1.5 * frequency
        elif any(keyword.lower() in token for token in prompt_tokens):
            score += 0.75
    score += math.log1p(sum(prompt_tokens.values())) * 0.1
    return score


def rank_scenarios(request: PromptRequest) -> ScenarioSuggestionResponse:
    tokens = Counter(_tokenize(request.prompt))
    options: List[ScenarioOption] = []
    for scenario_id, spec in SCENARIO_CATALOG.items():
        score = _score(tokens, spec.keywords)
        if request.user_profile:
            if request.user_profile.get("risk_profile") == "conservative" and "volatility" in spec.keywords:
                score *= 0.8
        options.append(
            ScenarioOption(
                scenario_id=scenario_id,
                title=spec.title,
                short_description=spec.short_description,
                rationale=spec.rationale,
                inputs=spec.inputs,
                methodology=spec.methodology,
                deliverables=spec.deliverables,
                score=round(score, 4),
            )
        )
    options.sort(key=lambda opt: opt.score, reverse=True)
    max_items = request.max_scenarios
    options = [opt for opt in options if opt.score > 0][:max_items] or options[:max_items]
    return ScenarioSuggestionResponse(
        prompt=request.prompt,
        options=options,
        metadata={"scored": len(options), "total_available": len(SCENARIO_CATALOG)},
    )
