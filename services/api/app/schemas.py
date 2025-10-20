"""Pydantic schemas shared across the API layer."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PromptRequest(BaseModel):
    """Incoming request payload for scenario suggestions."""

    prompt: str = Field(..., description="User supplied natural-language goal")
    user_profile: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional user context (e.g., preferences, constraints) forwarded to the orchestrator.",
    )
    max_scenarios: int = Field(
        default=5,
        ge=1,
        le=12,
        description="Maximum number of ranked scenarios to return for the prompt.",
    )


class ScenarioOption(BaseModel):
    """Canonical description of a scenario available to the user."""

    scenario_id: str
    title: str
    short_description: str
    rationale: str
    inputs: List[str]
    methodology: List[str]
    deliverables: List[str]
    score: float = Field(..., ge=0.0, description="Relative relevance score used for ranking")


class ScenarioSuggestionResponse(BaseModel):
    """Response envelope returned to the client for prompt suggestions."""

    prompt: str
    options: List[ScenarioOption]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ScenarioExecutionRequest(BaseModel):
    """Request payload used to trigger a concrete scenario analysis run."""

    scenario_id: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    user_profile: Optional[Dict[str, Any]] = None


class ScenarioExecutionResponse(BaseModel):
    """Response payload returned when a scenario run has been scheduled."""

    run_id: str
    status: str
    message: str
    scenario_id: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class PredictRequest(BaseModel):
    """Legacy prediction endpoint request body."""

    symbol: str
    last5: Optional[List[float]] = Field(default=None, description="Previous five observations for quick scoring")
