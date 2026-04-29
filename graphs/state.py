from __future__ import annotations

from typing import TypedDict


class ResearchState(TypedDict):
    query: str
    city: str
    raw_docs: list[str]
    weather_data: dict
    transport_data: dict
    analysis: str
    final_report: str
    error: str | None


class ReviewState(TypedDict):
    topic: str
    draft: str
    feedback: str
    iteration: int
    approved: bool
    quality_score: int | None
