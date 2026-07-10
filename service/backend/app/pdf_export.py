from __future__ import annotations

from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .draft_service import FIELD_ID_TO_LABEL
from .models import AnswerResponse, DraftResponse


def _register_korean_font() -> str:
    candidates = [
        Path("C:/Windows/Fonts/malgun.ttf"),
        Path("C:/Windows/Fonts/malgunbd.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            try:
                pdfmetrics.registerFont(TTFont("MalgunGothic", str(candidate)))
                return "MalgunGothic"
            except Exception:
                continue
    return "Helvetica"


def build_draft_pdf(answer_payload: AnswerResponse, draft_payload: DraftResponse, form_name: str | None = None, form_id: str | None = None) -> bytes:
    buffer = BytesIO()
    font_name = _register_korean_font()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="재외공관 민원서식 초안",
    )

    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    body_style = styles["BodyText"]
    section_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        fontName=font_name,
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#6f3b16"),
        spaceAfter=8,
    )
    meta_style = ParagraphStyle(
        "Meta",
        parent=body_style,
        fontName=font_name,
        fontSize=10.5,
        leading=15,
    )
    body_style.fontName = font_name
    title_style.fontName = font_name

    story = [
        Paragraph("재외공관 민원서식 초안", title_style),
        Spacer(1, 6),
        Paragraph(f"민원 분야: {answer_payload.classification.category or '-'}", meta_style),
        Paragraph(f"국가: {answer_payload.classification.country or '-'}", meta_style),
        Paragraph(f"관할 공관: {answer_payload.classification.mission or '-'}", meta_style),
        Paragraph(f"민원명: {answer_payload.classification.title or '-'}", meta_style),
        Spacer(1, 12),
    ]

    if draft_payload.form_drafts:
        for current_form_name, values in draft_payload.form_drafts.items():
            form_meta = next((form for form in draft_payload.required_forms if form.form_name == current_form_name), None)
            if form_name and current_form_name != form_name:
                continue
            if form_id and (not form_meta or form_meta.form_id != form_id):
                continue
            story.append(Paragraph(current_form_name, section_style))
            table_rows = [["항목", "입력값"]]
            for label, value in values.items():
                table_rows.append([label, value])
            if len(table_rows) == 1:
                table_rows.append(["안내", "입력된 값이 아직 없습니다."])
            table = Table(table_rows, colWidths=[55 * mm, 105 * mm], repeatRows=1)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0e3d2")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                        ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#ccb49d")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("FONTNAME", (0, 0), (-1, 0), font_name),
                        ("FONTNAME", (0, 1), (-1, -1), font_name),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor("#fbf7f1")]),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 7),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ]
                )
            )
            story.append(table)
            field_options = getattr(form_meta, "field_options", {}) if form_meta else {}
            if field_options:
                option_rows = [["선택 항목", "예시"]]
                for field_id, options in field_options.items():
                    if not options:
                        continue
                    option_rows.append([FIELD_ID_TO_LABEL.get(field_id, field_id), " / ".join(options)])
                if len(option_rows) > 1:
                    story.append(Spacer(1, 4))
                    option_table = Table(option_rows, colWidths=[55 * mm, 105 * mm], repeatRows=1)
                    option_table.setStyle(
                        TableStyle(
                            [
                                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f6eadb")),
                                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dcc5ac")),
                                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                ("FONTNAME", (0, 0), (-1, 0), font_name),
                                ("FONTNAME", (0, 1), (-1, -1), font_name),
                                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fcf8f2")]),
                                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                                ("TOPPADDING", (0, 0), (-1, -1), 6),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                            ]
                        )
                    )
                    story.append(option_table)
            story.append(Spacer(1, 12))

    if draft_payload.remaining_fields:
        story.append(Paragraph("추가로 필요한 항목", section_style))
        for field_id in draft_payload.remaining_fields:
            story.append(Paragraph(f"- {field_id}", body_style))
        story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            "이 문서는 제출용 원본이 아니라 입력 초안 정리본입니다. 서명, 날짜, 기관 작성란은 현장에서 최종 확인이 필요합니다.",
            body_style,
        )
    )

    document.build(story)
    return buffer.getvalue()
