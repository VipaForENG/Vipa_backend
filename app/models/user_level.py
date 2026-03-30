from sqlalchemy import Column, Integer, String, Float, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from app.core.database import Base

class UserLevel(Base):
    __tablename__ = "user_levels"

    user_level_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    cefr_level = Column(String(10))                   # 최종 판정 레벨 (A1~C2)
    overall_score = Column(Float, default=0.0)       # 레벨 테스트 종합 점수
    update_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())