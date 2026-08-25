# app/models/user.py
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, SmallInteger, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    # 모든 컬럼을 Mapped 타입 힌팅과 mapped_column으로 통일
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # 소셜 로그인을 위해 비밀번호와 닉네임은 Optional(Nullable) 처리
    password: Mapped[Optional[str]] = mapped_column(String(255))
    nickname: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    
    # 프로필 이미지 URL 또는 로컬 경로를 저장하기 위한 컬럼
    profile_image: Mapped[Optional[str]] = mapped_column(String(255))
    
    social_role: Mapped[int] = mapped_column(SmallInteger, default=0)
    is_social: Mapped[int] = mapped_column(Integer, default=0)
    study_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # 비밀번호 재설정용 인증 코드
    reset_code: Mapped[Optional[str]] = mapped_column(String(10))
    # 코드 만료 시간
    reset_code_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))