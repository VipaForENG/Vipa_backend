from sqlalchemy import Column, Integer, TEXT, ForeignKey, TIMESTAMP, JSON
from sqlalchemy.sql import func
from app.core.database import Base

class LevelTestResult(Base):
    __tablename__ = "level_test_results"

    test_id = Column(Integer, primary_key=True)
    user_level_id = Column(Integer, ForeignKey("user_levels.user_level_id", ondelete="CASCADE"), nullable=False)
    
    # GPT-5의 상세 분석 데이터 (JSONB 매핑)
    raw_analysis_json = Column(JSON)                 
    weakness_tags = Column(TEXT)                     # 취약점 태그 (시제 오류, 어휘 부족 등)
    created_at = Column(TIMESTAMP, server_default=func.now())