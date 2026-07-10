from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from .data_loader import load_known_metadata
from .models import ClassificationResult, ConversationContext, SearchResult


ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env")

NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "openai/gpt-oss-20b")
NVIDIA_TIMEOUT_SECONDS = float(os.getenv("NVIDIA_TIMEOUT_SECONDS", "90"))
NVIDIA_MAX_TOKENS = int(os.getenv("NVIDIA_MAX_TOKENS", "700"))


def is_llm_configured() -> bool:
    return bool(os.getenv("NVIDIA_API_KEY"))


@lru_cache(maxsize=1)
def get_llm_client() -> OpenAI:
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY is not configured")
    return OpenAI(
        base_url=NVIDIA_BASE_URL,
        api_key=api_key,
        timeout=NVIDIA_TIMEOUT_SECONDS,
        max_retries=1,
    )


def classify_with_llm(
    user_query: str,
    context: ConversationContext | None,
    local_hint: ClassificationResult,
) -> ClassificationResult:
    metadata = load_known_metadata()
    context_payload = context.model_dump() if context else None
    hint_payload = local_hint.model_dump()
    system_prompt = f"""
당신은 재외공관 민원 및 사건사고 질문을 분류하는 AI입니다.
반드시 제공된 출력 스키마에 맞춰 한국어 질문을 구조화하세요.

허용 route:
- civil_service: 일반 민원
- emergency_manual: 사건사고·긴급 대응
- needs_clarification: 민원 유형이나 관할 정보를 특정할 수 없음

허용 category:
- 여권
- 재외국민등록
- 공증·영사확인
- 가족관계
- 병역
- 사건사고

알려진 국가: {", ".join(sorted(metadata["countries"]))}
알려진 공관: {", ".join(sorted(metadata["missions"]))}

규칙:
1. 여권 분실과 일반 도난이 함께 있으면 출국에 필요한 여권 민원을 우선합니다.
2. 국가나 공관을 알 수 없으면 추측하지 말고 null로 둡니다.
3. title과 record_id는 로컬 힌트가 질문과 명확히 일치할 때만 사용합니다.
4. 이전 대화 맥락이 있으면 짧은 후속 질문에도 기존 민원 정보를 유지합니다.
5. 공관이 필요한 일반 민원인데 공관을 특정할 수 없으면 needs_followup을 true로 설정합니다.
6. reasoning에는 판단 근거를 짧은 문장으로 작성합니다.
""".strip()
    user_prompt = json.dumps(
        {
            "user_query": user_query,
            "conversation_context": context_payload,
            "local_candidate_hint": hint_payload,
        },
        ensure_ascii=False,
    )
    response = get_llm_client().beta.chat.completions.parse(
        model=NVIDIA_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format=ClassificationResult,
    )
    parsed = response.choices[0].message.parsed
    if parsed is None:
        raise RuntimeError("NVIDIA API returned no parsed classification")
    return parsed


def generate_grounded_answer(
    query: str,
    classification: ClassificationResult,
    results: list[SearchResult],
    context: ConversationContext | None,
) -> str:
    evidence = [
        {
            "chunk_id": result.chunk_id,
            "record_id": result.record_id,
            "metadata": result.metadata,
            "content": result.content[:2500],
        }
        for result in results[:3]
    ]
    system_prompt = """
당신은 재외공관 민원 안내 AI입니다. 반드시 제공된 검색 근거만 사용해 한국어로 답변하세요.

답변 규칙:
1. 사용자의 상황을 먼저 한 문장으로 정리합니다.
2. 필요한 절차, 준비사항, 다음 행동을 구체적인 목록으로 안내합니다.
3. 근거에 없는 수수료, 처리기간, 서류, 법률 해석을 만들어내지 않습니다.
4. 근거가 불충분하거나 최신 확인이 필요한 내용은 반드시 "공관 확인 필요"라고 표시합니다.
5. 긴급 사건사고는 신변 안전 확보와 현지 긴급기관 연락을 우선 안내합니다.
6. 검색 근거의 chunk_id나 내부 record_id는 본문에 노출하지 않습니다.
7. 제출용 서식을 실제로 완성했다고 표현하지 않습니다.
8. Markdown 제목 기호나 굵게 표시는 사용하지 말고, 짧은 소제목과 하이픈 목록으로 작성합니다.
9. 하이픈 목록은 반드시 항목마다 새 줄에 작성합니다. 한 문단 안에 " - "로 여러 항목을 이어 쓰지 않습니다.
""".strip()
    user_prompt = json.dumps(
        {
            "user_query": query,
            "classification": classification.model_dump(),
            "conversation_context": context.model_dump() if context else None,
            "retrieved_evidence": evidence,
        },
        ensure_ascii=False,
    )
    response = get_llm_client().chat.completions.create(
        model=NVIDIA_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=NVIDIA_MAX_TOKENS,
        temperature=0.2,
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("NVIDIA API returned an empty answer")
    cleaned = re.sub(r"^\s*#{1,6}\s*", "", content, flags=re.MULTILINE)
    cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"\s+-\s+", "\n- ", cleaned)
    cleaned = re.sub(r"\s+(?=\d+\.\s)", "\n", cleaned)
    return cleaned.strip()
