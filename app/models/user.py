# user 테이블 모델 정의한것. 
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, DateTime, Integer, String, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False)
    password = Column(String(255))
    nickname = Column(String(100), unique=True)
    social_role = Column(SmallInteger, default=0)  # PostgreSQL SMALLINT 사용
    is_social = Column(Integer, default=0)
    study_count = Column(Integer, default=0)
    # 비밀번호 재설정용 인증 코드 (6자리 숫자 등)
    reset_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    # 코드 만료 시간 (보통 생성 후 5~10분)
    reset_code_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # 관계 설정 (로봇 설정과 1:1 연결)
    robot = relationship("RobotControl", back_populates="owner", uselist=False, cascade="all, delete-orphan")