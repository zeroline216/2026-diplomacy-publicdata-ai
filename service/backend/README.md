# backend MVP

`raw_data`에 있는 최종 RAG JSONL, 테스트셋, forms schema/policy를 읽고 NVIDIA의 OpenAI 호환 API로 분류와 근거 기반 답변을 생성하는 FastAPI 백엔드입니다.

## 포함 기능

- `/classify`: NVIDIA LLM으로 질문을 민원 카테고리와 공관 단위로 분류
- `/search`: 분류 결과를 바탕으로 로컬 JSONL 검색
- `/answer`: NVIDIA LLM이 근거 청크 범위에서 답변하고 공관/안전 정보를 결합
- `/draft`: forms schema/policy 기반 서식 추천
- `/chat`: 분류 1회로 답변과 서식 추천을 함께 생성
- `/meta`: 현재 적재된 메타데이터 요약
- `/`: 챗봇형 정적 프론트엔드

## 실행

저장소 루트의 `.env`에 NVIDIA API 키를 설정합니다.

```text
NVIDIA_API_KEY=...
NVIDIA_MODEL=openai/gpt-oss-20b
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_TIMEOUT_SECONDS=90
NVIDIA_MAX_TOKENS=700
```

API 키를 제외한 항목은 생략할 수 있습니다. 기본 모델은 지연시간을 줄이기 위해 `openai/gpt-oss-20b`를 사용합니다.

```bash
cd service/backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

실행 후 아래 주소를 열면 됩니다.

```text
http://127.0.0.1:8000/
```

PDF 내보내기를 쓰려면 `reportlab`이 설치되어 있어야 하며, `requirements.txt`에 포함되어 있습니다.

## 예시 요청

```bash
curl -X POST http://127.0.0.1:8000/answer ^
  -H "Content-Type: application/json" ^
  -d "{\"user_query\":\"미국 시애틀에서 여권을 잃어버렸고 다음 주에 한국에 가야 해. 뭘 준비해야 해?\"}"
```

## 테스트셋 평가

로컬 분류기와 검색기를 테스트셋 62문항으로 한 번에 채점할 수 있습니다.

```bash
cd service/backend
.venv\Scripts\activate
python evaluate_local.py
```

결과:

- 터미널에 `route/category/country/mission/title/record` 정확도 출력
- 상세 리포트 저장: `service/backend/evaluation_report.json`

## 다음 연결 순서

1. 현재 로컬 점수 기반 `retriever.py`를 벡터DB 검색기로 교체
2. LLM 분류·답변 품질을 테스트셋으로 평가
3. 필요하면 현재 정적 UI를 React UI로 교체

NVIDIA API 호출이 실패하거나 키가 없으면 서비스 중단 대신 기존 로컬 분류·답변 방식으로 폴백합니다.
