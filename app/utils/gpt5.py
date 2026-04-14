# app/utils/gpt5.py
import os
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv
from typing import List, Iterable
from openai.types.chat import ChatCompletionMessageParam

# 환경 변수 로드 (.env 파일에서 API 키를 가져옵니다)
load_dotenv()

# 비동기 클라이언트 인스턴스 생성
# 2026년 기준 최신 SDK 방식입니다.
client = AsyncOpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)

# 사용할 모델명
MODEL_NAME = "gpt-5.4-mini" 

async def generate_test_questions() -> list:
    """
    GPT API를 호출하여 CEFR A1~C2 레벨이 혼합된 20문항을 JSON 배열 형태로 생성합니다.
    """
    # 1. 프롬프트 설계 (JSON 구조를 명확히 지시)
    system_prompt = """
    당신은 20년 경력의 전문 영어 교육학자이자 CEFR 레벨 평가 전문가입니다.
    사용자의 영어 실력을 측정하기 위한 20개의 객관식 빈칸 추론 문제를 생성해야 합니다.
    
    [조건]
    1. CEFR 레벨(A1, A2, B1, B2, C1, C2)이 골고루 섞이도록 출제하세요.
    2. 모든 문장은 실용적인 현대 영어 회화 및 비즈니스 상황을 반영해야 합니다.
    3. 반드시 아래 JSON 스키마를 엄격하게 준수하여 응답하세요. (다른 말은 절대 추가하지 마세요)
    4. 각 문제는 고유한 ID, CEFR 레벨, 영어 문장(빈칸 포함), 4개의 선택지, 정답, 그리고 한국어 번역을 포함해야 합니다.
    [JSON 스키마 형태]
    {
        "questions": [
            {
                "id": 1,
                "cefr_level": "A1",
                "question": "I ___ a student at the university.",
                "options": ["am", "is", "are", "be"],
                "answer": "am",
                "korean_translation": "나는 대학교 학생입니다."
            }
        ]
    }
    """

    try:
        # 2. 비동기 API 호출 (JSON 모드 활성화)
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "지금 바로 20개의 레벨 테스트 문항을 생성해줘."}
            ],
            response_format={"type": "json_object"}, # 핵심: JSON 응답 강제
            temperature=0.7 # 너무 창의적이지도, 너무 뻔하지도 않은 적절한 수치
        )
        
        # 3. 응답 결과 파싱
        raw_content = response.choices[0].message.content
        
        # Pylance 에러 해결: raw_content가 None일 경우 예외를 발생시켜 except 블록으로 보냄
        if raw_content is None:
            raise ValueError("GPT-5 응답에 내용(content)이 없습니다.")
            
        parsed_data = json.loads(raw_content)
        
        return parsed_data.get("questions", [])

    except Exception as e:
        print(f"GPT 질문 생성 중 에러 발생: {e}")
        # 에러 발생 시 앱이 뻗지 않도록 최소한의 기본 문항 반환 (Fallback)
        return [
            {
                "id": 1, "cefr_level": "A1", 
                "question": "Error ___ occurred.", "options": ["has", "have"], 
                "answer": "has", "korean_translation": "에러가 발생했습니다."
            }
        ]


async def analyze_user_answers(user_answers: list) -> dict:
    """
    [2단계] 유저가 제출한 20개의 답변을 분석하여 CEFR 레벨과 상세 JSON 프로필을 반환합니다.
    """
    # 1. 프론트엔드에서 넘어온 리스트 데이터를 AI가 읽기 좋게 문자열로 변환
    answers_text = json.dumps(user_answers, ensure_ascii=False, indent=2)

    # 2. 초정밀 프롬프트 설계 (AI에게 채점 기준과 반환 스키마를 강제합니다)
    system_prompt = """
    당신은 20년 경력의 깐깐하고 정확한 원어민 영어 평가자입니다.
    사용자가 푼 20개의 영어 문제(객관식 빈칸 추론 등) 답변 데이터가 주어집니다. 
    이 데이터를 분석하여 사용자의 CEFR 레벨과 상세한 성적 프로필을 반드시 아래 JSON 형식으로만 반환하세요.

    [평가 기준]
    - 정답률, 문법(grammar) 오류 유형, 어휘(vocabulary) 수준을 종합적으로 판단하세요.
    - 취약점 태그(weakness_tags)는 "시제오류", "전치사미숙", "어휘부족", "도치구문취약" 같이 핵심 단어 2~4개를 쉼표(,)로 구분하여 작성하세요.
    - 전체 점수(overall_score)는 100점 만점 기준으로 산정하세요.

    [필수 JSON 스키마 형태]
    {
        "cefr_level": "B1",  // A1, A2, B1, B2, C1, C2 중 하나
        "overall_score": 75.5,
        "raw_analysis_json": {
            "correct_answers_count": 15,
            "grammar_score": 70,
            "vocabulary_score": 80,
            "detailed_feedback": "현재 완료 시제 사용에 취약함을 보임. B2 수준의 도치 구문을 전혀 이해하지 못함. 하지만 기초적인 A1~A2 수준의 일상 대화 문법은 완벽함."
        },
        "weakness_tags": "시제오류, 고급도치미숙"
    }
    """

    try:
        # 3. 비동기 API 호출 (JSON 응답 강제)
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"다음 사용자의 답변 데이터를 정밀 분석해줘:\n{answers_text}"}
            ],
            response_format={"type": "json_object"},
            # 🔥 채점과 분석은 창의성보다 '정확성/일관성'이 중요하므로 온도를 낮춥니다.
            temperature=0.2 
        )
        
        raw_content = response.choices[0].message.content
        
        # Pylance 에러 방어막
        if raw_content is None:
            raise ValueError("GPT-5 응답에 내용(content)이 없습니다.")
            
        parsed_data = json.loads(raw_content)
        
        # 4. 라우터가 기대하는 딕셔너리 형태로 안전하게 파싱하여 반환
        return {
            "cefr_level": parsed_data.get("cefr_level", "A1"),
            "overall_score": float(parsed_data.get("overall_score", 0.0)),
            "raw_analysis_json": parsed_data.get("raw_analysis_json", {}),
            "weakness_tags": parsed_data.get("weakness_tags", "데이터 부족")
        }

    except Exception as e:
        print(f"답변 분석 중 에러 발생: {e}")
        # 에러 발생 시 시스템 멈춤 방지용 기본값 (Fallback)
        return {
            "cefr_level": "A1",
            "overall_score": 0.0,
            "raw_analysis_json": {"error": "분석 중 서버 에러가 발생했습니다.", "details": str(e)},
            "weakness_tags": "평가불가"
        }
    
# 실시간 대화 처리 함수
async def get_chat_response(user_message: str, history: list, cefr_level: str) -> dict:
    """
    [3단계] 실시간 대화 처리
    유저의 CEFR 레벨(A1~C2)에 맞춰 답변 난이도를 조절합니다.
    """
    system_prompt = f"""
    You are VIPA, a friendly AI English tutor.
    User's CEFR Level: {cefr_level} 
    
    [Rules]
    1. Strictly adjust your vocabulary and grammar complexity to the user's CEFR level ({cefr_level}).
    2. Provide a natural English response and its Korean translation.
    3. Briefly correct the user's grammar only if there's a significant error.
    4. MUST respond in JSON format.
    
    [JSON Schema]
    {{
        "en": "AI's English response",
        "ko": "Korean translation",
        "feedback": "Concise grammar feedback or 'Perfect!'",
        "understanding_score": 0-100
    }}
    """

    try:
        # 대화 기록(history)에 현재 메시지 추가하여 맥락 유지
        messages: List[ChatCompletionMessageParam] = [
        {"role": "system", "content": system_prompt}]
        # 최신 대화 5개만 유지 (토큰 절약)
        for msg in history[-5:]:
            messages.append({
                "role": msg.get("role", "user"), 
                "content": msg.get("content", "")
            })
        messages.append({"role": "user", "content": user_message})

        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            response_format={"type": "json_object"},
            max_completion_tokens=150,  # 응답 길이 제한 (토큰 절약)
            temperature=0.8
        )

        raw_content = response.choices[0].message.content
        if raw_content is None: raise ValueError("No content")
            
        return json.loads(raw_content)

    except Exception as e:
        print(f"Chat Error: {e}")
        return {
            "en": "I'm sorry, I'm having trouble connecting.",
            "ko": "죄송해요, 연결에 문제가 발생했습니다.",
            "feedback": "N/A",
            "understanding_score": 0
        }