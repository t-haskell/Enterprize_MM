"""Pydantic models used by the orchestration service."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PromptRequest(BaseModel):
    prompt: str
    user_profile: Optional[Dict[str, Any]] = None
    max_scenarios: int = Field(default=5, ge=1, le=12)


class ScenarioOption(BaseModel):
    scenario_id: str
    title: str
    short_description: str
    rationale: str
    inputs: List[str]
    methodology: List[str]
    deliverables: List[str]
    score: float


class ScenarioSuggestionResponse(BaseModel):
    prompt: str
    options: List[ScenarioOption]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ScenarioExecutionRequest(BaseModel):
    scenario_id: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    user_profile: Optional[Dict[str, Any]] = None


class ScenarioExecutionResponse(BaseModel):
    run_id: str
    status: str
    message: str
    scenario_id: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ScenarioSpec(BaseModel):
    scenario_id: str
    title: str
    short_description: str
    rationale: str
    inputs: List[str]
    methodology: List[str]
    deliverables: List[str]
    keywords: List[str]
    tags: List[str]
    embedding: List[float]
    restricted_regions: List[str] = Field(default_factory=list)
    eligibility_tags: List[str] = Field(default_factory=list)
    requires_accreditation: bool = False
    complexity: str = Field(default="intermediate")
