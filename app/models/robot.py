from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, ForeignKey, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User

class RobotControl(Base):
    __tablename__ = "robot_control"

    # 기본키, 외래키 (null 불가능하므로 Optional 안 씀)
    robot_id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), unique=True)
    
    # 일반 컬럼들
    robot_ip: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_auto_connect: Mapped[bool] = mapped_column(default=False)
    
    energy_level: Mapped[int] = mapped_column(default=100)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    
    motor_pitch_angle: Mapped[int] = mapped_column(default=90)
    motor_yaw_angle: Mapped[int] = mapped_column(default=90)

    # 유저 테이블과 연결 (타입 힌트는 문자열로 클래스명 명시)
    owner: Mapped["User"] = relationship("User", back_populates="robot")