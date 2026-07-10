from __future__ import annotations

import json
from pathlib import Path

from app.classifier import classify_query
from app.data_loader import load_testset
from app.models import ConversationContext
from app.retriever import retrieve


ROOT_DIR = Path(__file__).resolve().parents[2]
OUTPUT_PATH = ROOT_DIR / "service" / "backend" / "evaluation_report.json"


def _safe_equal(left: str | None, right: str | None) -> bool:
    return (left or None) == (right or None)


def evaluate() -> dict:
    testset = load_testset()
    cases = testset["cases"]

    summary = {
        "total_cases": len(cases),
        "route_correct": 0,
        "category_correct": 0,
        "country_correct": 0,
        "mission_correct": 0,
        "title_correct": 0,
        "record_top1_correct": 0,
        "record_top3_hit": 0,
    }
    details: list[dict] = []

    for case in cases:
        query = case["user_query"]
        expected = case["expected"]
        classification = classify_query(query, ConversationContext())
        results = retrieve(query, classification, top_k=3)
        top1_record_id = results[0].record_id if results else None
        top3_record_ids = [result.record_id for result in results]

        route_correct = _safe_equal(classification.route, expected.get("route"))
        category_correct = _safe_equal(classification.category, expected.get("category"))
        country_correct = _safe_equal(classification.country, expected.get("country"))
        mission_correct = _safe_equal(classification.mission, expected.get("mission"))
        title_correct = _safe_equal(classification.title, expected.get("title"))
        record_top1_correct = _safe_equal(top1_record_id, expected.get("record_id"))
        record_top3_hit = expected.get("record_id") in top3_record_ids if expected.get("record_id") else not results

        summary["route_correct"] += int(route_correct)
        summary["category_correct"] += int(category_correct)
        summary["country_correct"] += int(country_correct)
        summary["mission_correct"] += int(mission_correct)
        summary["title_correct"] += int(title_correct)
        summary["record_top1_correct"] += int(record_top1_correct)
        summary["record_top3_hit"] += int(record_top3_hit)

        details.append(
            {
                "id": case["id"],
                "query": query,
                "expected": expected,
                "predicted": {
                    "route": classification.route,
                    "category": classification.category,
                    "country": classification.country,
                    "mission": classification.mission,
                    "title": classification.title,
                    "record_top1": top1_record_id,
                    "record_top3": top3_record_ids,
                },
                "correct": {
                    "route": route_correct,
                    "category": category_correct,
                    "country": country_correct,
                    "mission": mission_correct,
                    "title": title_correct,
                    "record_top1": record_top1_correct,
                    "record_top3": record_top3_hit,
                },
            }
        )

    accuracy = {
        key: round(value / summary["total_cases"] * 100, 1)
        for key, value in summary.items()
        if key != "total_cases"
    }
    report = {
        "summary": summary,
        "accuracy_percent": accuracy,
        "details": details,
    }
    return report


def main() -> None:
    report = evaluate()
    OUTPUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=== Local Evaluation Summary ===")
    for key, value in report["accuracy_percent"].items():
        print(f"{key}: {value}%")
    print(f"saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
