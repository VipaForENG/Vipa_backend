from typing import Optional
from datetime import datetime
from sqlalchemy import TEXT, ForeignKey, TIMESTAMP, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.core.database import Base

class VocabLearningDetail(Base):
    """
    유저의 개별 문제 풀이 세션 로그 이력을 기록하는 테이블입니다.
    """
    __tablename__ = "vocab_learning_detail"

    learning_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    vocab_id: Mapped[int] = mapped_column(ForeignKey("vocabulary.vocab_id", ondelete="CASCADE"), nullable=False)
    
    # O/X 분기 및 결과창 매핑 가속을 위한 플래그
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
    # 오답 기록을 담을 가변 텍스트 컬럼
    user_answer: Mapped[Optional[str]] = mapped_column(TEXT, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())