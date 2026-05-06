from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, SmallInteger, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.robot import RobotControl

if TYPE_CHECKING:
    from app.models.robot import RobotControl

class User(Base):
    __tablename__ = "users"

    # 모든 컬럼을 Mapped 타입 힌팅과 mapped_column으로 통일하여 Pylance 에러를 원천 차단합니다.
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # 소셜 로그인을 위해 비밀번호와 닉네임은 Optional(Nullable) 처리
    password: Mapped[Optional[str]] = mapped_column(String(255))
    nickname: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    
    social_role: Mapped[int] = mapped_column(SmallInteger, default=0)
    is_social: Mapped[int] = mapped_column(Integer, default=0)
    study_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # 비밀번호 재설정용 인증 코드 (6자리 숫자 등)
    reset_code: Mapped[Optional[str]] = mapped_column(String(10))
    # 코드 만료 시간 (보통 생성 후 5~10분)
    reset_code_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # 관계 설정 (로봇 설정과 1:1 연결)
    # 팁: 문자열로 클래스명을 적으면 순환 참조(Circular Import) 에러를 막을 수 있습니다.
    robot: Mapped[Optional["RobotControl"]] = relationship(
        "RobotControl", 
        back_populates="owner", 
        uselist=False, 
        cascade="all, delete-orphan"
    )