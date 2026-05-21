from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class RecentSessionItem(BaseModel):
    session_id: int
    scenario_title: str
    category: str
    created_at: datetime
    audio_url: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class AiCorrectionItem(BaseModel):
    turn_id: int
    session_id: int
    user_input: str
    corrected_en: str
    feedback_ko: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CategoryProgressItem(BaseModel):
    category: str
    completed_sessions: int


class ConversationDashboardResponse(BaseModel):
    recent_sessions: List[RecentSessionItem]
    ai_corrections: List[AiCorrectionItem]
    category_progress: List[CategoryProgressItem]
