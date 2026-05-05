import openai
from app.core.config import settings # env 파일 로드

async def generate_chat_opening(cefr_level: str, ai_role: str):
    """
    유저 레벨과 역할을 기반으로 GPT에게 시나리오 생성을 요청합니다.
    """
    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    system_prompt = f"""
    You are an AI English tutor. 
    User Level: CEFR {cefr_level}
    Role: {ai_role}
    Task: Start a conversation suitable for the user's level.
    Constraints: Use simple grammar for A1-A2, complex for B2-C1. 
    Format: Return only 'English script | Korean translation'.
    """
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini", # 사용자 명칭 GPT-5.4-mini
        messages=[{"role": "system", "content": system_prompt}],
        temperature=0.7
    )
    
    return response.choices[0].message.content, system_prompt