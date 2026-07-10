from __future__ import annotations

import re
import logging

from .enrichment import find_homepage_info, find_office_info, find_safety_notices, find_travel_alerts
from .llm_service import generate_grounded_answer, is_llm_configured
from .models import AnswerResponse, ClassificationResult, ConversationContext, SearchResult


LOGGER = logging.getLogger(__name__)

DISCLAIMER = "원문에 없는 수수료·최신 구비서류·법률해석은 임의 보완하지 않았습니다. 최신 정보는 실제 공관 확인이 필요합니다."

ROUTE_LABELS = {
    "civil_service": "일반 민원",
    "emergency_manual": "사건사고 대응",
    "needs_clarification": "추가 확인 필요",
}


def _clean_excerpt(text: str, limit: int = 320) -> str:
    text = re.sub(r"\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[#*`]+", " ", text)
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line in {"[일반 민원]", "국가", "공관", "민원명", "민원분류"}:
            continue
        if len(line) <= 2:
            continue
        lines.append(line)
    cleaned = " ".join(lines)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:limit].rstrip()


def _build_answer_text(
    query: str,
    classification: ClassificationResult,
    results: list[SearchResult],
    context: ConversationContext | None,
) -> str:
    if classification.route == "needs_clarification":
        followups = "\n".join(f"- {item}" for item in classification.followup_questions)
        return f"정확한 공관 또는 민원명을 특정하려면 추가 정보가 필요합니다.\n{followups}"

    if context and any(keyword in query for keyword in ["서식", "작성", "초안", "기입", "채워", "입력"]):
        title = classification.title or context.title or "해당 민원 서식"
        return (
            f"네, 가능합니다. 현재 대화 맥락상 {title} 관련 서식을 이어서 도와드릴 수 있습니다.\n"
            "필수 정보가 준비되면 어떤 칸에 무엇을 써야 하는지 한국어로 순서대로 안내하고, 빠진 정보도 함께 정리해드립니다."
        )

    if not results:
        return "현재 로컬 코퍼스에서 바로 연결되는 근거를 찾지 못했습니다. 공관명과 체류 도시를 다시 확인해 주세요."

    if context and context.collected_fields:
        return "입력해주신 정보를 초안에 반영했습니다. 아래 서식 초안을 확인한 뒤 남은 항목만 이어서 입력해 주세요."

    top = results[0]
    metadata = top.metadata
    route_label = ROUTE_LABELS.get(classification.route, classification.route)
    category = metadata.get("category") or classification.category or "민원"
    mission = metadata.get("mission") or classification.mission or "관할 공관 확인 필요"
    title = metadata.get("title") or classification.title or "세부 민원명 확인 필요"
    excerpt = _clean_excerpt(top.content)

    lines = [
        f"{route_label}으로 분류되었고, 현재 질문은 {category} 관련 안내입니다.",
        f"관할 공관 기준은 {mission}입니다.",
        f"확인된 민원명은 {title}입니다.",
    ]
    if excerpt:
        lines.extend(["", f"핵심 안내: {excerpt}"])
    lines.extend(
        [
            "",
            "안내 원칙:",
            "- 검색된 원문 근거 범위 안에서만 답변합니다.",
            "- 세부 서류나 수수료가 불명확하면 공관 확인 필요로 표시합니다.",
        ]
    )
    return "\n".join(lines)


def build_answer(
    query: str,
    classification: ClassificationResult,
    results: list[SearchResult],
    context: ConversationContext | None = None,
) -> AnswerResponse:
    office_info = find_office_info(classification.mission)
    homepage_info = find_homepage_info(classification.mission)
    if office_info and homepage_info:
        office_info = {**office_info, "homepage": homepage_info}

    suggested_next_steps: list[str] = []
    if classification.category == "여권" and "분실" in (classification.title or ""):
        suggested_next_steps = [
            "분실 일자와 분실 장소를 먼저 확인합니다.",
            "여권분실신고서와 여권발급신청서에 들어갈 인적사항을 준비합니다.",
            "긴급 출국 여부와 경찰 신고 여부를 확인합니다.",
        ]

    answer_text = _build_answer_text(query, classification, results, context)
    if is_llm_configured() and classification.route != "needs_clarification" and results:
        try:
            answer_text = generate_grounded_answer(query, classification, results, context)
        except Exception as error:
            LOGGER.warning("NVIDIA LLM answer generation failed; using local fallback: %s", error)

    return AnswerResponse(
        classification=classification,
        answer=answer_text,
        citations=results[:3],
        office_info=office_info,
        safety_notices=find_safety_notices(classification.country),
        travel_alerts=find_travel_alerts(classification.country),
        disclaimer=DISCLAIMER,
        suggested_next_steps=suggested_next_steps,
    )
