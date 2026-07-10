from __future__ import annotations

from typing import Any

from .data_loader import load_embassy_data


def _iter_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("data", "items", "result", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def find_office_info(mission: str | None) -> dict[str, Any] | None:
    if not mission:
        return None
    dataset = load_embassy_data()
    for item in _iter_records(dataset["embassy"]):
        text = " ".join(str(value) for value in item.values())
        if mission in text:
            return item
    return None


def find_homepage_info(mission: str | None) -> dict[str, Any] | None:
    if not mission:
        return None
    dataset = load_embassy_data()
    for item in _iter_records(dataset["homepage"]):
        text = " ".join(str(value) for value in item.values())
        if mission in text:
            return item
    return None


def find_safety_notices(country: str | None) -> list[dict[str, Any]]:
    if not country:
        return []
    dataset = load_embassy_data()
    matches: list[dict[str, Any]] = []
    for item in _iter_records(dataset["safety_notice"]):
        text = " ".join(str(value) for value in item.values())
        if country in text:
            matches.append(item)
    return matches[:3]


def find_travel_alerts(country: str | None) -> list[dict[str, Any]]:
    if not country:
        return []
    dataset = load_embassy_data()
    matches: list[dict[str, Any]] = []
    for item in _iter_records(dataset["travel_alert"]):
        text = " ".join(str(value) for value in item.values())
        if country in text:
            matches.append(item)
    return matches[:3]
