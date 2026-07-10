from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from .answer_service import build_answer
from .classifier import classify_query
from .data_loader import load_known_metadata, load_rag_chunks, load_testset
from .draft_service import build_draft_response
from .models import AnswerResponse, ChatResponse, DraftResponse, PdfExportRequest, QueryRequest, SearchResponse
from .retriever import retrieve


app = FastAPI(
    title="Diplomacy Public Data AI MVP",
    version="0.1.0",
    description="재외공관 민원 분류, RAG 검색, 서식 추천을 위한 FastAPI MVP",
)

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def frontend() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/meta")
def meta() -> dict[str, object]:
    metadata = load_known_metadata()
    return {
        "categories": sorted(metadata["categories"]),
        "countries": sorted(metadata["countries"]),
        "missions_count": len(metadata["missions"]),
        "titles_count": len(metadata["titles"]),
        "chunk_count": len(load_rag_chunks()),
    }


@app.post("/classify")
def classify(request: QueryRequest):
    return classify_query(request.user_query, request.context)


@app.post("/search", response_model=SearchResponse)
def search(request: QueryRequest) -> SearchResponse:
    classification = classify_query(request.user_query, request.context)
    results = retrieve(request.user_query, classification, top_k=request.top_k)
    return SearchResponse(classification=classification, results=results)


@app.post("/answer", response_model=AnswerResponse)
def answer(request: QueryRequest) -> AnswerResponse:
    classification = classify_query(request.user_query, request.context)
    results = retrieve(request.user_query, classification, top_k=request.top_k)
    return build_answer(request.user_query, classification, results, request.context)


def _find_draft_template(record_id: str | None) -> str | None:
    if not record_id:
        return None
    for case in load_testset().get("cases", []):
        if case.get("expected", {}).get("record_id") == record_id:
            return case.get("expected", {}).get("draft_template")
    return None


@app.post("/draft", response_model=DraftResponse)
def draft(request: QueryRequest) -> DraftResponse:
    classification = classify_query(request.user_query, request.context)
    draft_template = _find_draft_template(classification.record_id)
    return build_draft_response(
        classification=classification,
        user_query=request.user_query,
        draft_template=draft_template,
        context=request.context,
    )


@app.post("/chat", response_model=ChatResponse)
def chat(request: QueryRequest) -> ChatResponse:
    classification = classify_query(request.user_query, request.context)
    results = retrieve(request.user_query, classification, top_k=request.top_k)
    answer_payload = build_answer(
        request.user_query,
        classification,
        results,
        request.context,
    )
    draft_payload = build_draft_response(
        classification=classification,
        user_query=request.user_query,
        draft_template=_find_draft_template(classification.record_id),
        context=request.context,
    )
    return ChatResponse(answer=answer_payload, draft=draft_payload)


@app.post("/export/pdf")
def export_pdf(request: PdfExportRequest) -> Response:
    try:
        from .pdf_export import build_draft_pdf
    except ModuleNotFoundError:
        return Response(
            content="PDF export dependency is missing. Install reportlab first.",
            status_code=503,
            media_type="text/plain; charset=utf-8",
        )

    classification = classify_query(request.user_query, request.context)
    results = retrieve(request.user_query, classification, top_k=request.top_k)
    answer_payload = build_answer(request.user_query, classification, results, request.context)

    draft_payload = build_draft_response(
        classification=classification,
        user_query=request.user_query,
        draft_template=_find_draft_template(classification.record_id),
        context=request.context,
    )
    pdf_bytes = build_draft_pdf(answer_payload, draft_payload, form_name=request.form_name, form_id=request.form_id)
    filename = "draft_form.pdf"
    if request.form_name:
        filename = f"{request.form_name}.pdf"
    encoded_filename = quote(filename)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=\"draft_form.pdf\"; filename*=UTF-8''{encoded_filename}"},
    )
