from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


# =========================================================================
# 1. 실전 회화 학습 내역 목록 조회 프로토콜
# =========================================================================
class RecentSessionItem(BaseModel):
    session_id: int
    scenario_title: str
    category: str
    created_at: datetime
    audio_url: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class ConversationDashboardResponse(BaseModel):
    """불필요한 통계 및 교정 리스트를 제거하고 세션 히스토리 목록만 담아 반환하는 스키마"""
    recent_sessions: List[RecentSessionItem]


# =========================================================================
# 2. [신규 추가] 특정 세션 상세 대화 스크립트 조회 프로토콜 (내보내기 연동용)
# =========================================================================
class ScriptLineItem(BaseModel):
    role: str                 # 발화자 구분 ('user' 또는 'assistant')
    original_text: str        # 발화 원문 (유저 말 또는 AI 대답)
    translated_text: Optional[str] = None  # 한국어 번역 (AI 발화일 때 주로 활용)
    corrected_text: Optional[str] = None   # 문법 교정 완료 문장 (유저 발화일 때만 활용)
    feedback_comment: Optional[str] = None # AI 뉘앙스/문법 피드백 내용
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ConversationScriptResponse(BaseModel):
    session_id: int
    scenario_title: str
    ai_passage_en: str     # ✨ 필수 추가
    ai_passage_ko: str     # ✨ 필수 추가
    full_turns: List[Any]  # ✨ 필수 추가
    scripts: List[dict]    # scripts를 담을 리스트

    class Config:
        from_attributes = True
