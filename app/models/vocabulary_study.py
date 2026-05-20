from typing import Optional
from datetime import datetime
from sqlalchemy import String, ForeignKey, TIMESTAMP, CheckConstraint, UniqueConstraint,Boolean,Column
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.core.database import Base

class VocabularyStudy(Base):
    """
    유저별 특정 단어의 숙련도 상태 스냅샷 테이블입니다.
    Mapped 구조 적용으로 정수형 덧셈 연산(+= 1) 시 발생하는 Pylance 연산자 에러를 원천 차단합니다.
    """
    __tablename__ = "vocabulary_study"

    study_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    vocab_id: Mapped[int] = mapped_column(ForeignKey("vocabulary.vocab_id", ondelete="CASCADE"), nullable=False)
    
    # 상태 변화 리터럴 바인딩을 위해 str 매핑 적용
    status: Mapped[str] = mapped_column(String(20), default='LEARNING')
    incorrect_count: Mapped[int] = mapped_column(default=0)
    
    # 시점 관리를 위한 datetime 구조 정의
    last_reviewed: Mapped[datetime] = mapped_column(
        TIMESTAMP, 
        server_default=func.now(), 
        onupdate=func.now()
    )

    is_bookmarked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # 데이터 무결성을 위한 기존 제약 조건 전적으로 유지
    __table_args__ = (
        CheckConstraint("status IN ('LEARNING', 'MASTERED', 'WRONG')", name="check_vocab_status"),
        UniqueConstraint("user_id", "vocab_id", name="uq_user_vocab_study"),
    )