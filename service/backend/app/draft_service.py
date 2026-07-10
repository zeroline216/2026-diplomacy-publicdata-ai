from __future__ import annotations

import re
from typing import Any

from .data_loader import load_form_policies, load_form_schemas
from .models import ClassificationResult, ConversationContext, DraftForm, DraftResponse


DRAFT_TEMPLATE_TO_INTENT = {
    "여권분실 경위서": "passport_loss",
    "공증 사유서": "general_notarial",
    "출생신고 초안": "birth_report",
    "병역 국외여행 기간연장 사유서": "military_extension",
}

FIELD_LABELS = {
    "성명(한글)": "name_ko",
    "신청인 성명(한글)": "applicant_name",
    "신청인 연락처": "applicant_phone",
    "applicant_phone": "applicant_phone",
    "applicant_contact": "applicant_contact",
    "신청인 이름": "applicant_name",
    "영문 성명": "name_en",
    "name_en": "name_en",
    "한글 성명": "name_ko",
    "name_ko": "name_ko",
    "신청인 주소": "applicant_address",
    "신청인 생년월일": "applicant_birth_date",
    "주민등록번호": "resident_registration_number",
    "신청인 주민등록번호": "resident_registration_number",
    "주민등록번호 또는 생년월일": "applicant_resident_registration_number_or_birth_date",
    "최초 입국일": "first_entry_date",
    "first_entry_date": "first_entry_date",
    "해외 거주 주소": "foreign_address",
    "foreign_address": "foreign_address",
    "해외 이메일": "foreign_email",
    "foreign_email": "foreign_email",
    "해외 연락처": "foreign_phone",
    "foreign_phone": "foreign_phone",
    "병역 사항": "military_status",
    "military_status": "military_status",
    "체류 목적": "stay_purpose",
    "stay_purpose": "stay_purpose",
    "체류 자격": "residence_status",
    "residence_status": "residence_status",
    "비상연락처 이름": "emergency_contact_name",
    "비상연락처 전화번호": "emergency_contact_phone",
    "비상연락처와의 관계": "emergency_contact_relation",
    "여권 종류": "passport_type",
    "면수": "passport_pages",
    "여권 유효기간": "passport_period",
    "유효기간": "passport_period",
    "여권번호": "passport_number",
    "여권 발급일자": "passport_issue_date",
    "발급일자": "passport_issue_date",
    "여권 만료일": "passport_expiry_date",
    "기간 만료일": "passport_expiry_date",
    "분실 일자": "loss_date",
    "분실 장소": "loss_place",
    "분실 사유": "loss_reason",
    "신고인 성명(한글)": "reporter_name_ko",
    "신고인 주민등록번호": "reporter_resident_registration_number",
    "신고인 주소": "reporter_address",
    "신고인 전화번호": "reporter_phone",
    "신고인 휴대전화": "reporter_mobile_phone",
    "신고자 한글 성명": "reporter_name_ko",
    "신고자 주민등록번호": "reporter_resident_registration_number",
    "신고자 주소": "reporter_address",
    "신고자 전화번호": "reporter_phone",
    "신고자 휴대전화": "reporter_mobile_phone",
    "미성년자 성명(한글)": "minor_name",
    "미성년자 주민등록번호": "minor_resident_registration_number",
    "미성년자 주소": "minor_address",
    "법정대리인 성명(한글)": "legal_representative_name",
    "법정대리인 이름": "legal_representative_name",
    "법정대리인 주민등록번호": "legal_representative_1_resident_registration_number",
    "법정대리인 주소": "legal_representative_1_address",
    "법정대리인과의 관계": "legal_representative_1_relationship",
    "대리인 성명(한글)": "agent_name",
    "대리인 연락처": "agent_phone",
    "위임 범위": "delegation_scope",
    "위임인 성명(한글)": "delegator_name",
    "위임인 생년월일": "delegator_birth_date",
    "위임인 주소": "delegator_address",
    "위임인과의 관계": "relationship_to_delegator",
    "신고인과의 관계": "proxy_relationship",
    "신청인과의 관계": "relationship_to_applicant",
    "대리인 주민등록번호": "proxy_resident_registration_number",
    "대리인 성명": "proxy_name",
    "대리인 이름": "proxy_name",
    "대리인 연락처": "proxy_contact",
    "작성자 성명": "writer_name",
    "작성자 연락처": "writer_phone",
    "작성일": "writer_date",
    "작성일자": "writer_date",
    "확인문구": "confirmation_statement",
    "여권 발급일": "passport_issue_date",
    "여권 만료일": "passport_expiry_date",
    "현재 여권번호": "current_passport_number",
    "현재 여권 발급일": "current_passport_issue_date",
    "현재 여권 만료일": "current_passport_expiry_date",
    "현재 로마자 성명": "current_romanized_name",
    "변경할 로마자 성명": "new_romanized_name",
    "현재 영문 성명": "current_english_name",
    "변경할 영문 성명": "new_english_name",
    "변경 사유": "change_reason_detail",
    "신청 부수": "requested_copy_count",
    "증명서 종류": "certificate_type",
    "신청 유형": "application_type",
    "우편 수령 주소": "mailing_address",
    "사용 목적": "usage_purpose",
    "점자여권 여부": "braille_passport",
}

FIELD_ID_TO_LABEL = {
    "applicant_phone": "신청인 연락처",
    "applicant_contact": "신청인 연락처",
    "applicant_name": "신청인 성명(한글)",
    "name_en": "영문 성명",
    "name_ko": "성명(한글)",
    "applicant_address": "신청인 주소",
    "applicant_birth_date": "신청인 생년월일",
    "resident_registration_number": "주민등록번호",
    "applicant_resident_registration_number_or_birth_date": "주민등록번호 또는 생년월일",
    "first_entry_date": "최초 입국일",
    "foreign_address": "해외 거주 주소",
    "foreign_email": "해외 이메일",
    "foreign_phone": "해외 연락처",
    "military_status": "병역 사항",
    "stay_purpose": "체류 목적",
    "residence_status": "체류 자격",
    "emergency_contact_name": "비상연락처 이름",
    "emergency_contact_phone": "비상연락처 전화번호",
    "emergency_contact_relation": "비상연락처와의 관계",
    "passport_type": "여권 종류",
    "passport_pages": "면수",
    "passport_period": "유효기간",
    "passport_number": "여권번호",
    "passport_issue_date": "발급일자",
    "passport_expiry_date": "기간 만료일",
    "loss_date": "분실 일자",
    "loss_place": "분실 장소",
    "loss_reason": "분실 사유",
    "reporter_name_ko": "신고인 성명(한글)",
    "reporter_resident_registration_number": "신고인 주민등록번호",
    "reporter_address": "신고인 주소",
    "reporter_phone": "신고인 전화번호",
    "reporter_mobile_phone": "신고인 휴대전화",
    "minor_name": "미성년자 성명(한글)",
    "minor_resident_registration_number": "미성년자 주민등록번호",
    "minor_address": "미성년자 주소",
    "legal_representative_name": "법정대리인 성명(한글)",
    "legal_representative_1_name": "법정대리인 1 성명(한글)",
    "legal_representative_1_resident_registration_number": "법정대리인 1 주민등록번호",
    "legal_representative_1_address": "법정대리인 1 주소",
    "legal_representative_1_relationship": "법정대리인과의 관계",
    "legal_representative_2_name": "법정대리인 2 성명(한글)",
    "legal_representative_2_resident_registration_number": "법정대리인 2 주민등록번호",
    "legal_representative_2_address": "법정대리인 2 주소",
    "legal_representative_2_relationship": "법정대리인 2와의 관계",
    "consent_type": "동의 유형",
    "agent_name": "대리인 성명(한글)",
    "agent_phone": "대리인 연락처",
    "delegation_scope": "위임 범위",
    "delegator_name": "위임인 성명(한글)",
    "delegator_birth_date": "위임인 생년월일",
    "delegator_address": "위임인 주소",
    "relationship_to_delegator": "위임인과의 관계",
    "relationship_to_applicant": "신청인과의 관계",
    "proxy_name": "대리인 성명(한글)",
    "proxy_name_ko": "대리인 성명(한글)",
    "proxy_contact": "대리인 연락처",
    "proxy_resident_registration_number": "대리인 주민등록번호",
    "proxy_relationship": "신고인과의 관계",
    "current_passport_number": "현재 여권번호",
    "current_passport_issue_date": "현재 여권 발급일",
    "current_passport_expiry_date": "현재 여권 만료일",
    "current_romanized_name": "현재 로마자 성명",
    "new_romanized_name": "변경할 로마자 성명",
    "current_english_name": "현재 영문 성명",
    "new_english_name": "변경할 영문 성명",
    "change_reason_detail": "변경 사유",
    "application_type": "신청 유형",
    "usage_purpose": "사용 목적",
    "requested_copy_count": "신청 부수",
    "certificate_type": "증명서 종류",
    "mailing_address": "우편 수령 주소",
    "writer_name": "작성자 성명",
    "writer_phone": "작성자 연락처",
    "birth_date": "생년월일",
    "address": "주소",
    "phone_number": "전화번호",
    "passport_expiry_period": "기간 만료일",
    "name": "성명(한글)",
    "confirmation_statement": "확인 문구",
    "delegation_type": "위임 유형",
    "mail_delivery_service": "우편수령 여부",
    "braille_passport": "점자여권 여부",
    "legal_representative_consent": "법정대리인 동의서",
    "passport_issue_application": "여권발급신청서",
    "passport_loss_report": "여권분실신고서",
    "passport_record_change_application": "여권 기재사항 변경신청서",
    "passport_fact_certificate_application": "여권사실증명서",
    "passport_copy_certificate_application": "여권사본증명서 발급신청서",
    "passport_invalid_confirmation_application": "여권실효확인신청서",
    "passport_issue_proxy_consent": "여권발급 위임장 및 동의서",
    "proxy_authorization": "대리수령 위임장",
}

FIELD_OPTION_EXAMPLES = {
    "passport_issue_application": {
        "passport_type": ["일반", "관용", "외교관", "긴급", "여행증명서(왕복)", "여행증명서(편도)"],
        "passport_pages": ["26면", "58면"],
        "passport_period": ["10년", "단수(1년)", "잔여기간", "5년", "5년 미만"],
    },
    "passport_issue_proxy_consent": {
        "delegation_type": ["여권 발급 신청", "여권 수령", "우편수령", "여권 분실 신고"],
        "mail_delivery_service": ["예", "아니오"],
        "braille_passport": ["예", "아니오"],
    },
}


def _is_minor_case(text: str) -> bool:
    return any(keyword in text for keyword in ["미성년", "18세 미만", "만 18세 미만", "아이", "자녀", "아들", "딸"])


def _is_proxy_case(text: str) -> bool:
    return any(keyword in text for keyword in ["대리", "위임", "대신", "법정대리인"])


def _infer_intent(classification: ClassificationResult, user_query: str, draft_template: str | None) -> str | None:
    if draft_template in DRAFT_TEMPLATE_TO_INTENT:
        return DRAFT_TEMPLATE_TO_INTENT[draft_template]

    if classification.category == "여권" and any(keyword in user_query for keyword in ["분실", "잃어버", "도난"]):
        if _is_minor_case(user_query):
            return "minor_passport_loss"
        return "passport_loss"
    if classification.category == "여권" and _is_minor_case(user_query):
        return "minor_passport"
    if classification.category == "여권" and ("우편수령" in user_query or "우편 수령" in user_query):
        return "mail_delivery"
    if classification.category == "여권" and _is_proxy_case(user_query):
        return "proxy_pickup_or_application"
    if classification.category == "여권" and ("영문성명" in user_query or "영문 성명" in user_query):
        return "english_name_change"
    if classification.category == "여권" and ("로마자" in user_query or "로마자성명" in user_query):
        return "romanized_name_change"
    if classification.category == "여권" and ("기재사항 변경" in user_query or "사증란 추가" in user_query or "구여권번호" in user_query):
        return "passport_record_change"
    if classification.category == "여권" and ("사실증명" in user_query):
        return "passport_fact_certificate"
    if classification.category == "여권" and ("사본증명" in user_query):
        return "passport_copy_certificate"
    if classification.category == "여권" and ("실효확인" in user_query):
        return "passport_invalid_confirmation"
    if classification.category == "여권" and ("재발급" in user_query or "발급" in user_query):
        return "passport_issue"
    if classification.category == "가족관계":
        return "family_relation_certificate"
    if classification.category == "재외국민등록":
        if "등본" in user_query:
            return "overseas_registration_certificate_copy"
        if "변경" in user_query or "이동" in user_query:
            return "overseas_registration_change_move"
        if "위임" in user_query or "대리" in user_query:
            return "overseas_registration_proxy"
        return "overseas_registration_apply"
    if classification.category == "병역":
        return "military_extension"
    if classification.category == "공증·영사확인":
        return "general_notarial"
    if classification.category == "출생신고":
        return "birth_report"
    return None


def _normalize_mission_name(policy: dict[str, Any], mission: str | None) -> str | None:
    if not mission:
        return None
    if mission in policy.get("exception_mission_forms", {}):
        return mission
    aliases = policy.get("mission_aliases", {})
    return aliases.get(mission, mission)


def _select_form_ids(
    policy: dict[str, Any],
    category: str,
    intent: str | None,
    mission: str | None,
    user_query: str,
) -> tuple[list[str], str | None]:
    resolved_mission = _normalize_mission_name(policy, mission)
    mission_rule = policy.get("exception_mission_forms", {}).get(resolved_mission or "")

    if mission_rule and mission_rule.get("required_forms"):
        selected = list(mission_rule["required_forms"])
        if intent == "overseas_registration_proxy" and "overseas_registration_proxy_authorization" not in selected:
            selected.append("overseas_registration_proxy_authorization")
        return list(dict.fromkeys(selected)), mission_rule.get("checklist_note")

    if intent and intent in policy.get("intent_to_form_rules", {}):
        selected = list(policy["intent_to_form_rules"][intent])
    else:
        selected = []

    default_forms = policy.get("default_forms", [])
    if not selected and default_forms:
        selected = [default_forms[0]["form_id"]]

    if mission_rule and mission_rule.get("available_forms"):
        available_forms = set(mission_rule["available_forms"])
        default_form_ids = {item["form_id"] for item in default_forms}
        selected = [form_id for form_id in selected if form_id in available_forms or form_id in default_form_ids]

    schema = load_form_schemas().get(category, {})
    forms = schema.get("forms", {})
    if not selected and forms:
        selected = [next(iter(forms.keys()))]

    if category == "여권":
        if any(keyword in user_query for keyword in ["분실", "잃어버", "도난"]):
            selected.extend(["passport_issue_application", "passport_loss_report"])
        if _is_minor_case(user_query):
            selected.append("legal_representative_consent")
        if _is_proxy_case(user_query):
            selected.append("proxy_authorization")

    return list(dict.fromkeys(selected)), mission_rule.get("checklist_note") if mission_rule else None


def _resolve_form_meta(schema: dict[str, Any], form_id: str) -> dict[str, Any] | None:
    forms = schema.get("forms", {})
    form_meta = forms.get(form_id)
    if not form_meta:
        return None
    parent_id = form_meta.get("inherits")
    if not parent_id:
        return dict(form_meta)
    parent_meta = _resolve_form_meta(schema, parent_id)
    if not parent_meta:
        return dict(form_meta)
    merged = dict(parent_meta)
    merged.update({key: value for key, value in form_meta.items() if key != "inherits"})
    return merged


def _collect_field_options(form_id: str, form_meta: dict[str, Any]) -> dict[str, list[str]]:
    options: dict[str, list[str]] = {}
    for key, value in form_meta.items():
        if not key.startswith("allowed_") or not isinstance(value, list):
            continue
        field_id = key.removeprefix("allowed_")
        options[field_id] = list(dict.fromkeys(str(item) for item in value))

    for field_id, values in FIELD_OPTION_EXAMPLES.get(form_id, {}).items():
        current = options.setdefault(field_id, [])
        for item in values:
            if item not in current:
                current.append(item)
    return options


def _match_first(text: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            value = match.group(1).strip()
            if value:
                return value
    return None


FIELD_PROPAGATION_GROUPS = [
    ["name_ko", "applicant_name", "reporter_name_ko", "writer_name"],
    ["resident_registration_number", "reporter_resident_registration_number", "applicant_resident_registration_number_or_birth_date"],
    ["applicant_phone", "applicant_contact", "reporter_phone", "reporter_mobile_phone", "writer_phone"],
    ["applicant_address", "reporter_address", "address", "foreign_address"],
    ["passport_number", "current_passport_number", "old_passport_number"],
    ["passport_issue_date", "current_passport_issue_date"],
    ["passport_expiry_date", "current_passport_expiry_date", "passport_expiry_period"],
    ["legal_representative_name", "legal_representative_1_name"],
    ["legal_representative_1_relationship", "relationship_to_applicant"],
    ["proxy_name", "proxy_name_ko", "agent_name"],
    ["proxy_contact", "agent_phone"],
]


def _propagate_collected_fields(collected: dict[str, str]) -> dict[str, str]:
    updated = dict(collected)
    for group in FIELD_PROPAGATION_GROUPS:
        value = next((updated[field_id] for field_id in group if updated.get(field_id)), None)
        if not value:
            continue
        for field_id in group:
            updated.setdefault(field_id, value)
    return updated


def _extract_user_fields(user_query: str, context: ConversationContext | None = None) -> dict[str, str]:
    collected = dict(context.collected_fields) if context else {}
    normalized = user_query.replace("\n", " ")
    labels = sorted(FIELD_LABELS.keys(), key=len, reverse=True)

    for index, label in enumerate(labels):
        pattern = re.escape(label) + r"\s*[:：]\s*"
        match = re.search(pattern, normalized)
        if not match:
            continue
        start = match.end()
        end = len(normalized)
        for other_label in labels:
            if other_label == label:
                continue
            next_match = re.search(rf"\s+{re.escape(other_label)}\s*[:：]\s*", normalized[start:])
            if next_match:
                end = min(end, start + next_match.start())
        value = normalized[start:end].strip(" ,")
        if value:
            collected[FIELD_LABELS[label]] = value

    json_like_pairs = re.findall(
        r'["\']?([A-Za-z가-힣][A-Za-z0-9_가-힣 ]{1,})["\']?\s*[:：]\s*["\']?([^,"\'}]+)["\']?',
        normalized,
    )
    for raw_key, raw_value in json_like_pairs:
        key = raw_key.strip()
        value = raw_value.strip()
        field_id = FIELD_LABELS.get(key)
        if field_id and value:
            collected[field_id] = value

    generic_name = _match_first(
        normalized,
        [
            r"(?:이름|성명)(?:은|은요|이|:|=|\s)\s*([가-힣]{2,5})",
            r"제\s*이름(?:은|은요|이|:|=|\s)\s*([가-힣]{2,5})",
        ],
    )
    if generic_name:
        for field_id in ["name_ko", "applicant_name", "reporter_name_ko", "writer_name"]:
            collected[field_id] = generic_name

    phone_match = _match_first(
        normalized,
        [
            r"(\+?\d[\d\s().-]{7,}\d)",
            r"(?:연락처|전화번호|휴대전화|휴대폰)(?:는|은|이|:|=|\s)\s*([+\d][\d\s().-]{7,}\d)",
        ],
    )
    if phone_match:
        phone_value = re.sub(r"\s+", "", phone_match)
        for field_id in [
            "applicant_phone",
            "reporter_phone",
            "reporter_mobile_phone",
            "emergency_contact_phone",
            "agent_phone",
            "proxy_contact",
            "writer_phone",
        ]:
            collected[field_id] = phone_value

    address_match = _match_first(
        normalized,
        [
            r"(?:주소|거주지|사는 곳|현주소)(?:는|은|이|:|=|\s)\s*([^\n,]+)",
            r"(?:주소는|거주지는|사는 곳은)\s*([^\n,]+)",
        ],
    )
    if address_match:
        for field_id in [
            "applicant_address",
            "reporter_address",
            "minor_address",
            "delegator_address",
            "mailing_address",
        ]:
            collected[field_id] = address_match.strip(" ,.")

    passport_type = next((choice for choice in ["일반", "관용", "외교관", "긴급", "여행증명서(왕복)", "여행증명서(편도)"] if choice in normalized), None)
    if passport_type:
        collected["passport_type"] = passport_type

    passport_pages = next((choice for choice in ["26면", "58면"] if choice in normalized), None)
    if passport_pages:
        collected["passport_pages"] = passport_pages

    passport_period = next((choice for choice in ["10년", "단수(1년)", "잔여기간", "5년", "5년 미만"] if choice in normalized), None)
    if passport_period:
        collected["passport_period"] = passport_period

    loss_place = _match_first(
        normalized,
        [
            r"(?:([가-힣A-Za-z0-9·\-\s]{2,50})에서)\s*(?:여권|지갑|휴대폰)?(?:을|을)?\s*(?:분실|잃어버|도난)",
            r"(?:분실 장소|장소)(?:는|은|이|:|=|\s)\s*([^\n,]+)",
        ],
    )
    if loss_place:
        collected["loss_place"] = loss_place.strip(" ,.")

    loss_reason = _match_first(
        normalized,
        [
            r"(?:분실 사유|사유)(?:는|은|이|:|=|\s)\s*([^\n,]+)",
        ],
    )
    if loss_reason:
        collected["loss_reason"] = loss_reason.strip(" ,.")
    elif any(keyword in normalized for keyword in ["떨어뜨", "잃어버", "분실", "도난"]):
        collected["loss_reason"] = "여권 분실"

    rrn_match = _match_first(
        normalized,
        [
            r"(?:주민등록번호|주민번호)(?:는|은|이|:|=|\s)\s*([0-9]{6}[- ]?[0-9]{7})",
        ],
    )
    if rrn_match:
        collected["resident_registration_number"] = rrn_match.replace(" ", "")

    passport_number = _match_first(
        normalized,
        [
            r"(?:여권번호|여권 번호)(?:는|은|이|:|=|\s)\s*([A-Za-z0-9]{5,20})",
        ],
    )
    if passport_number:
        collected["passport_number"] = passport_number.upper()

    date_patterns = [
        ("loss_date", [r"(?:분실 일자|분실일|잃어버린 날)(?:는|은|이|:|=|\s)\s*([0-9]{4}[./-][0-9]{1,2}[./-][0-9]{1,2})"]),
        ("passport_issue_date", [r"(?:발급일자|발급일|여권 발급일)(?:는|은|이|:|=|\s)\s*([0-9]{4}[./-][0-9]{1,2}[./-][0-9]{1,2})"]),
        ("passport_expiry_date", [r"(?:만료일|기간 만료일|여권 만료일)(?:는|은|이|:|=|\s)\s*([0-9]{4}[./-][0-9]{1,2}[./-][0-9]{1,2})"]),
        ("birth_date", [r"(?:생년월일|생년월일은|생일)(?:는|은|이|:|=|\s)\s*([0-9]{4}[./-][0-9]{1,2}[./-][0-9]{1,2}|[0-9]{6})"]),
    ]
    for field_id, patterns in date_patterns:
        date_value = _match_first(normalized, patterns)
        if date_value:
            collected[field_id] = date_value

    return _propagate_collected_fields(collected)


def build_draft_response(
    classification: ClassificationResult,
    user_query: str,
    draft_template: str | None = None,
    context: ConversationContext | None = None,
) -> DraftResponse:
    effective_category = classification.category or (context.category if context else None)

    if not effective_category:
        return DraftResponse(
            classification=classification,
            draft_template=draft_template,
            guidance=["카테고리가 확정되지 않아 초안 서식을 추천할 수 없습니다."],
            ready_to_fill=False,
            collected_fields=dict(context.collected_fields) if context else {},
        )

    schemas = load_form_schemas()
    policies = load_form_policies()
    schema = schemas.get(effective_category)
    policy = policies.get(effective_category)

    if not schema or not policy:
        return DraftResponse(
            classification=classification,
            draft_template=draft_template,
            guidance=["이 카테고리에 대한 서식 schema/policy가 아직 연결되지 않았습니다."],
            ready_to_fill=False,
            collected_fields=dict(context.collected_fields) if context else {},
        )

    effective_classification = classification.model_copy(update={"category": effective_category})
    intent = _infer_intent(effective_classification, user_query, draft_template)
    form_ids, mission_checklist_note = _select_form_ids(
        policy,
        effective_category,
        intent,
        classification.mission or (context.mission if context else None),
        user_query,
    )
    collected_fields = _extract_user_fields(user_query, context)

    forms: list[DraftForm] = []
    missing_fields: list[str] = []
    form_drafts: dict[str, dict[str, str]] = {}
    for form_id in form_ids:
        form_meta = _resolve_form_meta(schema, form_id)
        if not form_meta:
            continue
        required_fields = form_meta.get("required_fields", [])
        forms.append(
            DraftForm(
                form_id=form_id,
                form_name=form_meta.get("form_name", form_id),
                source_file=form_meta.get("source_file"),
                form_type=form_meta.get("form_type"),
                form_path=f"raw_data/{schema.get('raw_form_dir', '')}{form_meta.get('source_file', '')}" if form_meta.get("source_file") else None,
                required_fields=required_fields,
                optional_fields=form_meta.get("optional_fields", []),
                user_confirmation_fields=form_meta.get("user_confirmation_fields", []),
                submission_documents=form_meta.get("submission_documents", []),
                checklist_items=form_meta.get("checklist_items", []),
                notes=[form_meta.get("description", "")] if form_meta.get("description") else [],
                field_options=_collect_field_options(form_id, form_meta),
            )
        )
        form_drafts[form_meta.get("form_name", form_id)] = {
            FIELD_ID_TO_LABEL.get(field_id, field_id): collected_fields.get(field_id, "")
            for field_id in required_fields
        }
        missing_fields.extend([field_id for field_id in required_fields if field_id not in collected_fields])

    guidance = [
        "기관 작성란, 접수번호, 심사란은 AI가 채우지 않습니다.",
        "사용자가 제공하지 않은 개인정보는 빈칸으로 남기고 추가 확인을 요청해야 합니다.",
    ]
    if effective_category == "여권" and any(keyword in user_query for keyword in ["분실", "잃어버", "도난"]):
        if not _is_minor_case(user_query):
            guidance.append("조건 확인: 신청인이 만 18세 이상 성인인지 확인해야 합니다. 미성년자이면 법정대리인 동의서를 추가 작성합니다.")
        if not _is_proxy_case(user_query):
            guidance.append("조건 확인: 본인 신고인지 대리 신고인지 확인해야 합니다. 대리 신고이면 위임장과 대리관계 증명서류가 필요합니다.")
    if mission_checklist_note:
        guidance.append(f"공관별 추가 안내: {mission_checklist_note}")
    guidance.extend(schema.get("common_judge_rules", [])[:3])
    remaining_fields = sorted(set(missing_fields))
    write_support_message = None
    if forms and not remaining_fields:
        write_support_message = "입력해주신 정보로 필수 항목을 모두 채울 수 있습니다. 아래 초안 값을 확인한 뒤 서명·날짜·기관 작성란만 현장에서 마무리하면 됩니다."
    elif forms:
        write_support_message = "받은 정보는 초안에 반영했습니다. 아래 남은 항목만 추가로 확인하면 됩니다."

    return DraftResponse(
        classification=classification,
        draft_template=draft_template,
        required_forms=forms,
        missing_fields=remaining_fields,
        guidance=guidance,
        ready_to_fill=bool(forms and not remaining_fields),
        write_support_message=write_support_message,
        collected_fields=collected_fields,
        remaining_fields=remaining_fields,
        form_drafts=form_drafts,
    )
