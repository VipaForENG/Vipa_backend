# app/models/summary.py 수정
from sqlalchemy import Column, Integer, String, Date, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from datetime import date

class DailyStudySummary(Base):
    __tablename__ = "daily_study_summary"

    # Mapped[]를 사용하여 타입을 명시하면 Pylance 에러가 사라집니다.
    summary_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    study_date: Mapped[date] = mapped_column(Date, index=True)
    type: Mapped[str] = mapped_column(String)
    total_energy: Mapped[int] = mapped_column(Integer, default=0)
    total_count: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint('user_id', 'study_date', 'type', name='_user_date_type_uc'),
    )