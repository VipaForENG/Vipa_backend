from sqlalchemy import Column, Integer, TEXT, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from app.core.database import Base

class VocabLearningDetail(Base):
    __tablename__ = "vocab_learning_detail"

    learning_id = Column(Integer, primary_key=True)         # 기록 고유 식별자 (PK)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False) # 유저 고유 아이디 (FK)
    vocab_id = Column(Integer, ForeignKey("vocabulary.vocab_id", ondelete="CASCADE"), nullable=False) # 학습한 단어/구문 ID (FK)
    
    # 오답 분석 데이터
    user_answer = Column(TEXT)                              # 사용자가 입력한 오답 유사어 또는 문장
    created_at = Column(TIMESTAMP, server_default=func.now()) # 기록 일시