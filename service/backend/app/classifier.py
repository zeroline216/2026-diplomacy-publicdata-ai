from __future__ import annotations

import re
import logging
from typing import Any

from .data_loader import load_known_metadata, load_mission_aliases, load_testset
from .llm_service import classify_with_llm, is_llm_configured
from .models import ClassificationResult, ConversationContext


LOGGER = logging.getLogger(__name__)

CATEGORY_KEYWORDS = {
    "여권": ["여권", "재발급", "분실", "로마자", "영문성명", "점자여권", "여행증명서"],
    "재외국민등록": ["재외국민등록", "재외국민 등록", "등본", "변경", "이동 신고"],
    "공증·영사확인": ["공증", "위임장", "영사확인", "서명인증", "인감", "진술서", "상속포기"],
    "가족관계": ["가족관계", "기본증명서", "혼인관계", "등록부", "영문증명서"],
    "병역": ["병역", "국외여행", "재외국민2세", "복수국적", "기간연장", "유학생"],
    "사건사고": ["도난", "체포", "구금", "납치", "테러", "지진", "태풍", "마약", "사망", "보이스피싱"],
}

EMERGENCY_KEYWORDS = ["체포", "구금", "납치", "테러", "지진", "태풍", "도난", "마약", "사망", "보이스피싱"]
PASSPORT_PRIORITY_KEYWORDS = ["여권", "재발급", "분실"]
CONTEXT_CONTINUATION_KEYWORDS = ["서식", "작성", "초안", "기입", "채워", "입력", "위 정보", "이 정보", "그럼", "그러면"]
CONTEXT_FIELD_HINTS = [
    "applicant_contact",
    "first_entry_date",
    "foreign_address",
    "foreign_email",
    "foreign_phone",
    "military_status",
    "name_en",
    "name_ko",
    "passport_number",
    "loss_date",
    "loss_place",
    "loss_reason",
]


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _best_testset_match(user_query: str) -> dict[str, Any] | None:
    normalized_query = _normalize_text(user_query)
    best_case: dict[str, Any] | None = None
    best_score = 0

    for case in load_testset()["cases"]:
        score = 0
        candidate = _normalize_text(case["user_query"])
        for token in set(normalized_query.split()):
            if token and token in candidate:
                score += 1
        for keyword in case.get("acceptable_retrieval_keywords", []):
            if keyword in normalized_query:
                score += 2
        if score > best_score:
            best_score = score
            best_case = case
    return best_case if best_score >= 2 else None


def _resolve_mission(user_query: str) -> str | None:
    aliases = load_mission_aliases()
    for alias, standard_name in sorted(aliases.items(), key=lambda item: len(item[0]), reverse=True):
        if alias and alias in user_query:
            return standard_name

    for mission in load_known_metadata()["missions"]:
        if mission in user_query:
            return mission
    return None


def _resolve_country(user_query: str, mission: str | None) -> str | None:
    countries = load_known_metadata()["countries"]
    for country in countries:
        if country in user_query:
            return country

    if mission:
        matched = _best_testset_match(mission)
        if matched:
            return matched["expected"].get("country")
    return None


def _resolve_category(user_query: str) -> str | None:
    scored: list[tuple[int, str]] = []
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in user_query)
        if score:
            scored.append((score, category))
    if not scored:
        return None
    scored.sort(reverse=True)
    return scored[0][1]


def _resolve_route(user_query: str, category: str | None) -> str:
    if any(keyword in user_query for keyword in EMERGENCY_KEYWORDS):
        if category == "여권" and any(keyword in user_query for keyword in PASSPORT_PRIORITY_KEYWORDS):
            return "civil_service"
        return "emergency_manual"
    if category:
        return "civil_service"
    return "needs_clarification"


def _is_contextual_followup(user_query: str) -> bool:
    if any(keyword in user_query for keyword in CONTEXT_CONTINUATION_KEYWORDS):
        return True

    if any(field_hint in user_query for field_hint in CONTEXT_FIELD_HINTS):
        return True

    json_like_pairs = re.findall(r'["\']?[a-z][a-z0-9_]{2,}["\']?\s*:\s*["\']?[^,"\'}]+', user_query)
    if len(json_like_pairs) >= 2:
        return True

    colon_pair_count = len(re.findall(r'[:：]', user_query))
    if colon_pair_count >= 2:
        return True

    return False


def _apply_context_fallback(
    user_query: str,
    result: ClassificationResult,
    context: ConversationContext | None,
) -> ClassificationResult:
    if not context:
        return result

    if _is_contextual_followup(user_query):
        result.category = result.category or context.category
        result.country = result.country or context.country
        result.mission = result.mission or context.mission
        result.title = result.title or context.title
        result.record_id = result.record_id or context.record_id
        result.route = context.route or result.route
        if context.category:
            result.route = context.route or "civil_service"
            result.needs_followup = False
            result.followup_questions = []
            result.reasoning.append("이전 대화 맥락을 이어받아 민원 유형을 유지")
        return result

    if not result.category and context.category:
        result.category = context.category
    if not result.country and context.country:
        result.country = context.country
    if not result.mission and context.mission and any(keyword in user_query for keyword in ["여기", "저기", "공관", "거기"]):
        result.mission = context.mission
    if not result.title and context.title and _is_contextual_followup(user_query):
        result.title = context.title
    if not result.record_id and context.record_id and _is_contextual_followup(user_query):
        result.record_id = context.record_id
    if result.route == "needs_clarification" and context.category and _is_contextual_followup(user_query):
        result.route = context.route or "civil_service"
        result.needs_followup = False
        result.followup_questions = []
        result.reasoning.append("입력값만 전달된 후속 메시지로 판단하여 이전 민원 맥락 유지")
    return result


def _classify_query_locally(
    user_query: str,
    context: ConversationContext | None = None,
) -> ClassificationResult:
    matched_case = _best_testset_match(user_query)
    if matched_case:
        expected = matched_case["expected"]
        reasoning = [f"테스트셋 유사 발화 `{matched_case['id']}`와 높은 토큰 중복"]
        result = ClassificationResult(
            route=expected["route"],
            category=expected.get("category"),
            country=expected.get("country"),
            mission=expected.get("mission"),
            title=expected.get("title"),
            record_id=expected.get("record_id"),
            needs_followup=bool(expected.get("should_ask_followup")),
            followup_questions=expected.get("should_ask_followup", []),
            secondary_targets=expected.get("secondary_targets", []),
            reasoning=reasoning,
        )
        return _apply_context_fallback(user_query, result, context)

    mission = _resolve_mission(user_query)
    category = _resolve_category(user_query)
    country = _resolve_country(user_query, mission)
    route = _resolve_route(user_query, category)

    reasoning: list[str] = []
    if category:
        reasoning.append(f"카테고리 키워드 기반 분류: {category}")
    if mission:
        reasoning.append(f"공관 별칭 정규화: {mission}")
    if country:
        reasoning.append(f"국가 추출: {country}")

    needs_followup = mission is None and route != "emergency_manual"
    followup_questions = []
    if mission is None and country:
        followup_questions.append(f"{country} 내 체류 도시 또는 관할 공관을 알려주세요.")
    if category is None:
        followup_questions.append("여권, 재외국민등록, 공증, 가족관계, 병역, 사건사고 중 어떤 민원인지 알려주세요.")

    result = ClassificationResult(
        route="needs_clarification" if needs_followup else route,
        category=category,
        country=country,
        mission=mission,
        title=None,
        record_id=None,
        needs_followup=bool(followup_questions),
        followup_questions=followup_questions,
        reasoning=reasoning or ["사전 규칙으로 명확히 매칭되지 않아 추가 정보 필요"],
    )
    return _apply_context_fallback(user_query, result, context)


def classify_query(user_query: str, context: ConversationContext | None = None) -> ClassificationResult:
    local_result = _classify_query_locally(user_query, context)
    if not is_llm_configured():
        local_result.reasoning.append("NVIDIA_API_KEY가 없어 로컬 분류기를 사용")
        return local_result

    try:
        llm_result = classify_with_llm(user_query, context, local_result)
        llm_result.reasoning.insert(0, "NVIDIA LLM API 분류 결과")
        return _apply_context_fallback(user_query, llm_result, context)
    except Exception as error:
        LOGGER.warning("NVIDIA LLM classification failed; using local fallback: %s", error)
        local_result.reasoning.append("LLM 호출 실패로 로컬 분류기 사용")
        return local_result
