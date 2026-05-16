# app/utils/gpt5.py
import os
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv
from typing import List
from openai.types.chat import ChatCompletionMessageParam
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

# 환경 변수 로드 (.env 파일에서 API 키를 가져옵니다)
load_dotenv()

# 비동기 클라이언트 인스턴스 생성
client = AsyncOpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)

# 사용할 모델명
MODEL_NAME = "gpt-5.4-mini" 

# ==========================================
# [DB 연동 뼈대] 실제 CRUD 로직으로 교체해야 할 부분
# ==========================================
async def get_daily_token_usage(db: AsyncSession, user_id: int) -> int:
    """
    TODO: 실제 DB 로직 연동 필요
    """
    return 0

async def update_daily_token_usage(db: AsyncSession, user_id: int, used_tokens: int) -> None:
    """
    TODO: 실제 DB 로직 연동 필요
    """
    print(f"[토큰 기록] 유저 {user_id}가 {used_tokens} 토큰을 추가로 사용했습니다.")
    pass
# ==========================================


async def generate_test_questions() -> list:
    """
    [1단계] GPT API를 호출하여 CEFR A1~C2 레벨이 혼합된 20문항을 JSON 배열 형태로 생성합니다.
    """
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
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "지금 바로 20개의 레벨 테스트 문항을 생성해줘."}
            ],
            response_format={"type": "json_object"}, 
            temperature=0.7 
        )
        
        raw_content = response.choices[0].message.content
        if raw_content is None:
            raise ValueError("GPT-5 응답에 내용(content)이 없습니다.")
            
        parsed_data = json.loads(raw_content)
        return parsed_data.get("questions", [])

    except Exception as e:
        print(f"GPT 질문 생성 중 에러 발생: {e}")
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
    answers_text = json.dumps(user_answers, ensure_ascii=False, indent=2)

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
        "cefr_level": "B1", 
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
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"다음 사용자의 답변 데이터를 정밀 분석해줘:\n{answers_text}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.2 
        )
        
        raw_content = response.choices[0].message.content
        if raw_content is None:
            raise ValueError("GPT-5 응답에 내용(content)이 없습니다.")
            
        parsed_data = json.loads(raw_content)
        return {
            "cefr_level": parsed_data.get("cefr_level", "A1"),
            "overall_score": float(parsed_data.get("overall_score", 0.0)),
            "raw_analysis_json": parsed_data.get("raw_analysis_json", {}),
            "weakness_tags": parsed_data.get("weakness_tags", "데이터 부족")
        }

    except Exception as e:
        print(f"답변 분석 중 에러 발생: {e}")
        return {
            "cefr_level": "A1",
            "overall_score": 0.0,
            "raw_analysis_json": {"error": "분석 중 서버 에러가 발생했습니다.", "details": str(e)},
            "weakness_tags": "평가불가"
        }
    
async def get_chat_response(db: AsyncSession, user_id: int, user_message: str, history: list, cefr_level: str, today: date) -> dict:
    """
    [3단계] 실시간 대화 처리 및 토큰 관리
    """
    daily_limit = 50000 
    # 🚨 [수정] db 파라미터 전달 추가
    current_usage = await get_daily_token_usage(db, user_id) 
    
    if current_usage >= daily_limit:
        return {
            "en": "You've reached your daily conversation limit. See you tomorrow!",
            "ko": "오늘의 대화 한도를 모두 사용하셨어요. 내일 또 만나요!",
            "feedback": "Limit Reached",
            "understanding_score": 0
        }
    
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
        messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt}
        ]
        
        # 최신 대화 5개만 유지 (컨텍스트 토큰 비용 절약)
        for msg in history[-5:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Pylance(OpenAI SDK) 에러 해결: 동적 문자열(str) 대신 명확한 Literal 주입
            if role == "assistant":
                messages.append({"role": "assistant", "content": content})
            else:
                messages.append({"role": "user", "content": content})
                
        messages.append({"role": "user", "content": user_message})

        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            response_format={"type": "json_object"},
            max_completion_tokens=400, 
            temperature=0.8
        )

        if response.usage:
            total_tokens_used = response.usage.total_tokens
            # 🚨 [수정] db 파라미터 전달 추가
            await update_daily_token_usage(db, user_id, total_tokens_used)

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
    

async def generate_wrong_answer_hint(target_word: str, user_answer: str, context_sentence: str) -> str:
    """
    [즉석 검증 엔진] 유저가 입력한 오답과 정답의 맥락적/사전적 뉘앙스 차이를 GPT가 분석하여 
    정답을 유추할 수 있도록 돕는 친절한 한국어 힌트를 생성합니다.
    
    Args:
        target_word (str): 문장의 실제 영어 정답 단어 (예: 'customer')
        user_answer (str): 사용자가 타이핑한 오답 단어 (예: 'guest')
        context_sentence (str): 마스킹되기 전의 전체 원본 영어 예문
        
    Returns:
        str: 유저에게 보여줄 1~2문장 내외의 정밀 피드백 힌트 메시지
    """
    
    # 1. 오답과 정답의 차이점을 정밀 추적하도록 설계된 AI 가이드 프롬프트
    system_prompt = """
    당신은 20년 경력의 전문 영어 교육학자이자, 학생의 사소한 단어 선택 차이를 교정해 주는 친절한 AI 튜터 'VIPA'입니다.
    사용자가 영어 문장의 빈칸 채우기 문제에서 정답 대신 유사한 다른 단어를 입력했습니다.
    제공된 [데이터]를 바탕으로, 유저가 입력한 오답과 진짜 정답 간의 결정적인 문맥적/사전적 뉘앙스 차이를 짚어주는 힌트를 작성하세요.

    [작성 규칙]
    1. 절대로 정답 단어(Target Word)를 힌트 텍스트 내에 직접적으로 노출하거나 스펠링 힌트를 주지 마세요.
    2. 유저가 입력한 오답(User Answer)의 정확한 한계점과 의미를 먼저 설명하세요.
    3. 제공된 예문(Context Sentence) 속 상황에서 왜 정답 단어가 훨씬 더 자연스럽고 올바른 표현인지 그 뉘앙스 차이를 설명하세요.
    4. 친절하고 부드러운 대화체 문장의 한국어로 작성하되, 반드시 1~2문장 이내로 명쾌하고 간결하게 끝마치세요.
    """

    user_content = f"""
    [데이터]
    - 원본 예문 (Context): {context_sentence}
    - 진짜 정답 (Target Word): {target_word}
    - 유저 오답 (User Answer): {user_answer}

    위 데이터를 기반으로 정답을 직접 말하지 않는 최적의 뉘앙스 교정 힌트를 한국어로 생성해줘.
    """

    try:
        # 2. GPT-5 비동기 API 채널 가동
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.4, # 힌트의 일관성과 정밀도를 위해 온도를 낮춤
            max_completion_tokens=200 # 짤막한 문장 출력을 유도하여 토큰 비용 최적화
        )
        
        # 3. 응답 텍스트 추출 및 데이터 검증
        hint_result = response.choices[0].message.content
        if hint_result is None:
            raise ValueError("GPT-5가 힌트 메시지를 생성하지 못했습니다.")
            
        return hint_result.strip()

    except Exception as e:
        # 4. 실시간 AI 통신 장애를 방지하기 위한 안전한 하드코딩 Fallback 선언
        print(f"오답 힌트 생성 중 엔지니어링 에러 발생: {e}")
        return f"입력하신 '{user_answer}'도 유사한 맥락일 수 있으나, 본 예문의 문맥에서는 다른 단어가 더 자연스럽습니다. 단어의 글자 수와 뜻을 다시 한번 고민해 보세요!"