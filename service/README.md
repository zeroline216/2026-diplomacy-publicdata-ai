# service 개발 시작점

현재 저장소에서 서비스 개발에 바로 연결할 때의 기준은 아래와 같습니다.

- 입력 데이터: `raw_data/rag/재외공관_민원_사건사고_RAG_JSONL_카테고리통일.jsonl`
- 평가 데이터: `raw_data/testset/재외공관_민원_RAG_테스트질문세트.json`
- 서식 데이터: `raw_data/forms/schemas/*.json`, `raw_data/forms/policies/*.json`
- 정형 데이터: `raw_data/embassy.json`, `raw_data/embassy_homepage.json`, `raw_data/safety_notice.json`, `raw_data/travel_alert.json`

## 현재 구조

```text
service/
  README.md
  backend/
    README.md
    requirements.txt
    app/
  frontend/
    index.html
    styles.css
    app.js
```

## 권장 다음 단계

1. `backend` 실행 후 `/classify`, `/search`, `/answer`, `/draft` 동작 확인
2. 현재 `frontend` 정적 UI로 기본 동작 확인
3. 규칙 기반 분류기를 LLM 기반 분류기로 교체
4. 로컬 검색기를 벡터DB 기반 검색기로 교체
