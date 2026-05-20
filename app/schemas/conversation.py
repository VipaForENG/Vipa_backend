from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

# 1. 최근 대화 세션
class RecentSessionItem(BaseModel):
    session_id: int
    scenario_title: str       # (예: 입국 심사)
    category: str             # (예: 여행)
    created_at: datetime
    audio_url: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# 2. AI 교정 받은 문장 (오답 노트)
class AiCorrectionItem(BaseModel):
    turn_id: int
    session_id: int
    user_input: str           # 유저의 틀린 문장
    corrected_en: str         # AI 교정 문장
    feedback_ko: str          # 교정 이유
    model_config = ConfigDict(from_attributes=True)

# 3. 카테고리별 학습 현황
class CategoryProgressItem(BaseModel):
    category: str
    completed_sessions: int   # 해당 카테고리 완료 횟수

class ConversationDashboardResponse(BaseModel):
    recent_sessions: List[RecentSessionItem]
    ai_corrections: List[AiCorrectionItem]
    category_progress: List[CategoryProgressItem]