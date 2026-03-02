"""Shared data models for policy and response contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class PolicyDecision:
    """Policy decision for a user query."""

    action: str
    rule_id: Optional[str]
    reason: str
    redirect_message: Optional[str] = None


@dataclass(frozen=True)
class QueryResponse:
    """Final query response returned by the pipeline."""

    answer: str
    sources: List[str]
    confidence: float
    policy_triggered: bool
