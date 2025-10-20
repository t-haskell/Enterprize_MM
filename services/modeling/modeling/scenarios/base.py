"""Base scenario definitions."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class ScenarioSpec:
    scenario_id: str
    title: str
    summary: str
    inputs: List[str]
    methodology: List[str]
    deliverables: List[str]
    keywords: List[str]


class Scenario(ABC):
    spec: ScenarioSpec

    @abstractmethod
    def run(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the scenario and return structured results."""

    def _ensure_required_inputs(self, parameters: Dict[str, Any]) -> None:
        missing = [field for field in self.spec.inputs if field not in parameters]
        if missing:
            raise ValueError(f"Missing required parameters: {', '.join(missing)}")
