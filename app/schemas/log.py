from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# 학습 내역 리스트 항목
class StudyLogResponse(BaseModel):
    studylog_id: int
    type: str  # 'CONVERSATION' or 'VOCABULARY'
    earned_energy: int
    created_at: datetime
    
    # 상세 조회를 위한 ID들
    session_id: Optional[int] = None
    study_id: Optional[int] = None

    class Config:
        from_attributes = True

# 대화 중 AI 피드백 문장 로그
class SentenceLogResponse(BaseModel):
    sentencelog_id: int
    original_text: str
    corrected_text: str
    feedback_comment: Optional[str] = None

    class Config:
        from_attributes = True