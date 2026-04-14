from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    user_message: str
    session_id: Optional[int] = None # 대화 세션 유지용

class ChatResponse(BaseModel):
    en_content: str   # AI의 영어 답변 (TTS용)
    ko_content: str   # 실시간 번역 결과 (UI 출력용)
    feedback: str     # 유저 문장에 대한 간단한 피드백 (선택 사항)
    earned_energy: int # 이번 대화로 얻은 에너지