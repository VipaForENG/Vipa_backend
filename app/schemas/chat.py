from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    """프론트엔드 -> 백엔드 (API 요청 데이터)"""
    user_message: str = Field(
        ..., 
        description="유저가 마이크/텍스트로 전송한 영어 메시지"
    )
    session_id: Optional[int] = Field(
        default=None, 
        description="대화 세션 유지용 (None일 경우 새로운 세션 생성, 값이 있으면 DB에서 이전 대화 기록을 불러옴)"
    )

class ChatResponse(BaseModel):
    """백엔드 -> 프론트엔드 (API 응답 데이터)"""
    en_content: str = Field(
        ..., 
        description="AI의 영어 답변 (프론트에서 TTS 음성 합성용으로 사용)"
    )
    ko_content: str = Field(
        ..., 
        description="영어 답변의 한국어 번역 (UI 화면 출력용)"
    )
    feedback: str = Field(
        ..., 
        description="유저 문장에 대한 간단한 피드백 또는 교정 내용"
    )
    earned_energy: int = Field(
        ..., 
        description="이번 턴의 대화로 획득한 로봇 에너지 포인트 (예: 10)"
    )
    
    # 🔥 앞서 구현한 토큰 제한 처리를 위해 유지
    is_limit_reached: bool = Field(
        default=False, 
        description="일일 대화 토큰 한도 초과 여부 (True면 프론트에서 팝업 띄움)"
    )