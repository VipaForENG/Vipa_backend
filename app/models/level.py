from sqlalchemy import Column, Integer, String, Float, ForeignKey, TIMESTAMP, JSON, TEXT
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class UserLevel(Base):
    __tablename__ = "user_levels"

    user_level_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    cefr_level = Column(String(10))                   # 최종 판정 레벨 (A1~C2)
    overall_score = Column(Float, default=0.0)       # 레벨 테스트 종합 점수
    update_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # 관계 설정
    test_results = relationship("LevelTestResult", back_populates="level_info", cascade="all, delete-orphan")

class LevelTestResult(Base):
    __tablename__ = "level_test_results"

    test_id = Column(Integer, primary_key=True)
    user_level_id = Column(Integer, ForeignKey("user_levels.user_level_id", ondelete="CASCADE"), nullable=False)
    
    # GPT-5의 상세 분석 데이터 (PostgreSQL JSONB 대응)
    raw_analysis_json = Column(JSON)                 
    weakness_tags = Column(TEXT)                     # 취약점 태그 (시제 오류 등)
    created_at = Column(TIMESTAMP, server_default=func.now())

    level_info = relationship("UserLevel", back_populates="test_results")