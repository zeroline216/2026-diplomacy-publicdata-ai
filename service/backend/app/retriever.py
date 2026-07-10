from __future__ import annotations

from collections import defaultdict
from typing import Any

from .data_loader import load_rag_chunks
from .models import ClassificationResult, SearchResult


def _score_chunk(query: str, classification: ClassificationResult, chunk: dict[str, Any]) -> float:
    metadata = chunk.get("metadata", {})
    content = chunk.get("content", "")
    score = 0.0

    if classification.route and classification.route == chunk.get("data_type"):
        score += 2.0
    if classification.route == "emergency_manual" and chunk.get("data_type") == "emergency_manual":
        score += 3.0
    if classification.route == "civil_service" and chunk.get("data_type") == "civil_service":
        score += 3.0
    if classification.category and metadata.get("category") == classification.category:
        score += 4.0
    if classification.country and metadata.get("country") == classification.country:
        score += 3.0
    if classification.mission and metadata.get("mission") == classification.mission:
        score += 5.0
    if classification.record_id and chunk.get("record_id") == classification.record_id:
        score += 8.0
    if classification.title and metadata.get("title") == classification.title:
        score += 4.0

    for token in query.split():
        if len(token) < 2:
            continue
        if token in content:
            score += 0.3
        if token in " ".join(str(value) for value in metadata.values() if isinstance(value, str)):
            score += 0.5
    return score


def retrieve(query: str, classification: ClassificationResult, top_k: int = 5) -> list[SearchResult]:
    scored: list[SearchResult] = []
    for chunk in load_rag_chunks():
        score = _score_chunk(query, classification, chunk)
        if score <= 0:
            continue
        scored.append(
            SearchResult(
                chunk_id=chunk["chunk_id"],
                record_id=chunk["record_id"],
                score=round(score, 3),
                content=chunk["content"],
                metadata=chunk["metadata"],
            )
        )

    deduped: dict[str, SearchResult] = {}
    for item in sorted(scored, key=lambda result: result.score, reverse=True):
        deduped.setdefault(item.record_id, item)

    return list(deduped.values())[:top_k]


def group_results_by_record(results: list[SearchResult]) -> dict[str, list[SearchResult]]:
    grouped: dict[str, list[SearchResult]] = defaultdict(list)
    for result in results:
        grouped[result.record_id].append(result)
    return grouped
