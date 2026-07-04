import json
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()  # .env 파일에서 환경 변수 로드

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY")
)
# ==========================================
# 1. 입출력 서식
# ==========================================
class ClassificationResult(BaseModel):
    route: str = Field(description="'civil_service', 'emergency_manual', 'needs_clarification' 중 하나")
    category: str = Field(description="'여권', '재외국민등록', '공증·영사확인', '가족관계', '병역', '사건사고' 중 택 1")
    country: Optional[str] = Field(None, description="체류 국가 (예: 일본)")
    country_code: Optional[str] = Field(None, description="국가 코드 (예: JP, US)")
    resolved_mission: Optional[str] = Field(None, description="관할 공관명 (예: 주삿포로대한민국 총영사관)")
    service_title: str = Field(description="구체적인 민원명 또는 사건명 (예: 재외국민등록 신청)")

# ==========================================
# 2. 분류 AI Agent 함수 (이곳의 프롬프트를 깎는 것이 핵심!)
# ==========================================
def classify_query(user_query: str) -> ClassificationResult:
    # AI가 똑똑하게 분류하도록 지시문을 계속 다듬어주세요!
    system_prompt = """
    당신은 재외공관 민원 및 사건사고 유형을 분류하는 전문 AI Agent입니다.
    사용자의 질문을 분석하여 다음 규칙에 따라 알맞은 정보를 추출하세요.
    
    [가장 중요한 필수 규칙]
    1. category(카테고리)는 반드시 아래 6가지 단어 중에서만 똑같이 텍스트로 골라야 합니다. 절대 임의로 영어나 다른 단어를 지어내지 마세요.
       - 선택지: '여권', '재외국민등록', '공증·영사확인', '가족관계', '병역', '사건사고'
       
    2. 국가나 공관이 명확하지 않다면 억지로 추측하지 말고 null로 처리하세요.
    3. 지갑 도난, 폭행, 납치, 자연재해 등 위급한 상황은 route를 'emergency_manual'로 분류하세요.
    4. 일반적인 서류 발급, 갱신, 신고 민원은 route를 'civil_service'로 분류하세요.
    5. 질문에 여권 분실과 일반 도난/사건사고가 섞여 있는 경우, 출국을 위해 가장 우선적으로 처리해야 하는 '여권' 카테고리로 분류하세요.
    """

    response = client.beta.chat.completions.parse(
        model="nvidia/nemotron-3-ultra-550b-a55b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ],
        response_format=ClassificationResult
    )
    return response.choices[0].message.parsed

# ==========================================
# 3. 자동 채점 루프 (모의고사 62개 풀기)
# ==========================================
def run_evaluation():
    print("🚀 [AI 분류 Agent 자동 채점 시작]...\n")
    
    # 1. 파일 로드
    with open("재외공관_민원_RAG_테스트질문세트.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    
    # 2. 'cases' 키를 사용해 62개 문제 리스트 가져오기
    cases_list = raw_data["cases"]
        
    total_cases = len(cases_list)
    correct_category_count = 0
    
    # 3. 문제 하나씩 돌면서 채점
    for idx, case in enumerate(cases_list, 1):
        query = case["user_query"]
        expected = case["expected"]
        
        # AI에게 문제 풀기 지시
        ai_result = classify_query(query)
        
        # 채점 기준: 카테고리를 정확히 맞추었는가?
        is_category_correct = (ai_result.category == expected["category"])
        
        if is_category_correct:
            correct_category_count += 1
            status = "✅ 정답"
        else:
            status = "❌ 오답"
            
        print(f"[{idx:02d}/{total_cases}] {status} | 질문: {query[:30]}...")
        
        # 오답인 경우 원인 분석을 위해 상세 출력
        if not is_category_correct:
            print(f"   ㄴ 🤖 AI 예측 : {ai_result.category}")
            print(f"   ㄴ 🎯 원래 정답 : {expected['category']}")
            print("-" * 50)

    # 최종 점수 계산
    accuracy = (correct_category_count / total_cases) * 100
    print("\n" + "="*50)
    print(f"🎯 최종 정답률: {correct_category_count}/{total_cases} ({accuracy:.1f}%)")
    print("="*50)

if __name__ == "__main__":
    run_evaluation()
