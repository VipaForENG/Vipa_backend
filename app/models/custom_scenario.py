# app/models/custom_scenario.py

from datetime import datetime
from typing import Optional
from sqlalchemy import Integer, String, TEXT, ForeignKey, TIMESTAMP, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.core.database import Base

class CustomScenario(Base):
    """
    GPT-5.4-mini가 생성한 사용자 맞춤형 시나리오 저장 테이블
    """
    __tablename__ = "custom_scenario"

    scenario_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    sub_cat_id: Mapped[int] = mapped_column(Integer, ForeignKey("sub_category.sub_cat_id"), nullable=False)
    test_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("level_test_results.test_id"), nullable=True)
    
    # 생성 시점의 난이도를 역정규화하여 저장 (성능 및 로그 목적)
    difficulty_level: Mapped[str] = mapped_column(String(10), nullable=False) 
    
    # AI에게 전달된 최종 프롬프트 기록
    ai_prompt_used: Mapped[str] = mapped_column(TEXT, nullable=False)
    
    # AI가 생성한 지문 (Flutter 연동을 위해 JSONB 권장: {"en": "...", "ko": "..."})
    generated_script: Mapped[dict] = mapped_column(JSON, nullable=False) 
    
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        server_default=func.now()
    )