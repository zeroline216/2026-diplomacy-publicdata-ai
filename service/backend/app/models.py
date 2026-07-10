from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ClassificationResult(BaseModel):
    route: str
    category: str | None = None
    country: str | None = None
    mission: str | None = None
    title: str | None = None
    record_id: str | None = None
    needs_followup: bool = False
    followup_questions: list[str] = Field(default_factory=list)
    secondary_targets: list[dict[str, Any]] = Field(default_factory=list)
    reasoning: list[str] = Field(default_factory=list)


class ConversationContext(BaseModel):
    category: str | None = None
    country: str | None = None
    mission: str | None = None
    title: str | None = None
    record_id: str | None = None
    route: str | None = None
    draft_template: str | None = None
    required_forms: list[str] = Field(default_factory=list)
    collected_fields: dict[str, str] = Field(default_factory=dict)


class QueryRequest(BaseModel):
    user_query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=10)
    context: ConversationContext | None = None


class PdfExportRequest(QueryRequest):
    form_name: str | None = None
    form_id: str | None = None


class SearchResult(BaseModel):
    chunk_id: str
    record_id: str
    score: float
    content: str
    metadata: dict[str, Any]


class SearchResponse(BaseModel):
    classification: ClassificationResult
    results: list[SearchResult]


class AnswerResponse(BaseModel):
    classification: ClassificationResult
    answer: str
    citations: list[SearchResult]
    office_info: dict[str, Any] | None = None
    safety_notices: list[dict[str, Any]] = Field(default_factory=list)
    travel_alerts: list[dict[str, Any]] = Field(default_factory=list)
    disclaimer: str
    suggested_next_steps: list[str] = Field(default_factory=list)


class DraftForm(BaseModel):
    form_id: str
    form_name: str
    source_file: str | None = None
    form_path: str | None = None
    form_type: str | None = None
    required_fields: list[str] = Field(default_factory=list)
    optional_fields: list[str] = Field(default_factory=list)
    user_confirmation_fields: list[str] = Field(default_factory=list)
    submission_documents: list[Any] = Field(default_factory=list)
    checklist_items: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    field_options: dict[str, list[str]] = Field(default_factory=dict)


class DraftResponse(BaseModel):
    classification: ClassificationResult
    draft_template: str | None = None
    required_forms: list[DraftForm] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    guidance: list[str] = Field(default_factory=list)
    ready_to_fill: bool = False
    write_support_message: str | None = None
    collected_fields: dict[str, str] = Field(default_factory=dict)
    remaining_fields: list[str] = Field(default_factory=list)
    form_drafts: dict[str, dict[str, str]] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    answer: AnswerResponse
    draft: DraftResponse
