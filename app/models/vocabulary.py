from sqlalchemy import Column, Integer, String, TEXT, Boolean
from app.core.database import Base

class Vocabulary(Base):
    __tablename__ = "vocabulary"

    vocab_id = Column(Integer, primary_key=True)
    target_word = Column(String(100), nullable=False)
    cefr_level = Column(String(10), nullable=False)
    test_id = Column(Integer, nullable=True) # 레벨 테스트 결과 ID 참조
    expression = Column(TEXT)                # 맞춤형 문장
    meaning = Column(TEXT)                   # 한국어 해석
    
    focus_point = Column(TEXT)               # 집중 훈련 포인트
    is_customized = Column(Boolean, default=False)