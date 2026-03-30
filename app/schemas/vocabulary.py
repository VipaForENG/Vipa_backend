from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# 어휘 기본 정보
class VocabularyBase(BaseModel):
    target_word: str
    cefr_level: str
    expression: Optional[str] = None
    meaning: Optional[str] = None
    focus_point: Optional[str] = None

# 서버가 앱으로 단어 정보를 줄 때
class VocabularyResponse(VocabularyBase):
    vocab_id: int
    is_customized: bool

    class Config:
        from_attributes = True

# 유저의 단어 학습 상태 업데이트 (퀴즈 채점 후)
class VocabularyStudyUpdate(BaseModel):
    vocab_id: int
    is_correct: bool
    user_answer: Optional[str] = None  # 오답 분석용