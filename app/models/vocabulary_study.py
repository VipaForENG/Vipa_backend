from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, CheckConstraint
from sqlalchemy.sql import func
from app.core.database import Base

class VocabularyStudy(Base):
    __tablename__ = "vocabulary_study"

    study_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    vocab_id = Column(Integer, ForeignKey("vocabulary.vocab_id", ondelete="CASCADE"), nullable=False)
    
    # 학습 상태 (LEARNING, MASTERED, WRONG)
    status = Column(String(20), default='LEARNING')
    
    incorrect_count = Column(Integer, default=0)
    last_reviewed = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # PostgreSQL의 CHECK 제약 조건 추가
    __table_args__ = (
        CheckConstraint("status IN ('LEARNING', 'MASTERED', 'WRONG')", name="check_vocab_status"),
    )