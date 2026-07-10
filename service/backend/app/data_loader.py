from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[3]
RAW_DATA_DIR = ROOT_DIR / "raw_data"
RAG_PATH = RAW_DATA_DIR / "rag" / "재외공관_민원_사건사고_RAG_JSONL_카테고리통일.jsonl"
TESTSET_PATH = RAW_DATA_DIR / "testset" / "재외공관_민원_RAG_테스트질문세트.json"
FORMS_DIR = RAW_DATA_DIR / "forms"


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _iter_jsonl(path: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


@lru_cache(maxsize=1)
def load_rag_chunks() -> list[dict[str, Any]]:
    return _iter_jsonl(RAG_PATH)


@lru_cache(maxsize=1)
def load_testset() -> dict[str, Any]:
    return _load_json(TESTSET_PATH)


@lru_cache(maxsize=1)
def load_form_schemas() -> dict[str, dict[str, Any]]:
    schemas: dict[str, dict[str, Any]] = {}
    for path in (FORMS_DIR / "schemas").glob("*.json"):
        data = _load_json(path)
        schemas[data["category"]] = data
    return schemas


@lru_cache(maxsize=1)
def load_form_policies() -> dict[str, dict[str, Any]]:
    policies: dict[str, dict[str, Any]] = {}
    for path in (FORMS_DIR / "policies").glob("*.json"):
        data = _load_json(path)
        policies[data["category"]] = data
    return policies


@lru_cache(maxsize=1)
def load_embassy_data() -> dict[str, Any]:
    return {
        "embassy": _load_json(RAW_DATA_DIR / "embassy.json"),
        "homepage": _load_json(RAW_DATA_DIR / "embassy_homepage.json"),
        "safety_notice": _load_json(RAW_DATA_DIR / "safety_notice.json"),
        "travel_alert": _load_json(RAW_DATA_DIR / "travel_alert.json"),
    }


@lru_cache(maxsize=1)
def load_mission_aliases() -> dict[str, str]:
    aliases: dict[str, str] = {}
    for policy in load_form_policies().values():
        aliases.update(policy.get("mission_aliases", {}))
    return aliases


@lru_cache(maxsize=1)
def load_known_metadata() -> dict[str, set[str]]:
    categories: set[str] = set()
    countries: set[str] = set()
    missions: set[str] = set()
    titles: set[str] = set()
    for chunk in load_rag_chunks():
        metadata = chunk.get("metadata", {})
        if metadata.get("category"):
            categories.add(metadata["category"])
        if metadata.get("country"):
            countries.add(metadata["country"])
        if metadata.get("mission"):
            missions.add(metadata["mission"])
        if metadata.get("title"):
            titles.add(metadata["title"])
    return {
        "categories": categories,
        "countries": countries,
        "missions": missions,
        "titles": titles,
    }
