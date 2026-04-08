from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Float, ForeignKey, TIMESTAMP, JSON, TEXT, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base

class UserLevel(Base):
    """
    유저의 현재 CEFR 레벨 정보를 담는 테이블
    """
    __tablename__ = "user_levels"

    user_level_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 1:1 관계를 위해 unique=True 설정
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.user_id", ondelete="CASCADE"), 
        unique=True, 
        nullable=False
    )
    cefr_level: Mapped[Optional[str]] = mapped_column(String(10))  # A1 ~ C2
    overall_score: Mapped[float] = mapped_column(Float, default=0.0)
    update_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )

    # 관계 설정: 한 유저는 여러 번의 테스트 결과 기록을 가질 수 있음
    test_results: Mapped[List["LevelTestResult"]] = relationship(
        "LevelTestResult", 
        back_populates="level_info", 
        cascade="all, delete-orphan"
    )


class LevelTestResult(Base):
    """
    GPT-5가 분석한 상세 테스트 결과 기록 테이블 (JSON 데이터 포함)
    """
    __tablename__ = "level_test_results"

    test_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_level_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("user_levels.user_level_id", ondelete="CASCADE"), 
        nullable=False
    )
    
    # GPT-5의 상세 분석 데이터 (PostgreSQL JSONB 대응)
    # dict 형태로 다루기 위해 Mapped[Optional[dict]] 사용
    raw_analysis_json: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # 분석 요약 태그 (예: "시제 혼동", "비즈니스 어휘 부족")
    weakness_tags: Mapped[Optional[str]] = mapped_column(TEXT)
    
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        server_default=func.now()
    )

    # 역방향 관계 설정
    level_info: Mapped["UserLevel"] = relationship("UserLevel", back_populates="test_results")