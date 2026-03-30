from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from app.core.database import Base

class RobotControl(Base):
    __tablename__ = "robot_control"

    robot_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    
    robot_ip = Column(String(20))
    is_auto_connect = Column(Boolean, nullable=False, default=False)
    
    energy_level = Column(Integer, nullable=False, default=100)
    last_sync_at = Column(TIMESTAMP)
    
    motor_pitch_angle = Column(Integer, nullable=False, default=90)
    motor_yaw_angle = Column(Integer, default=90)

    # 유저 테이블과 연결
    owner = relationship("User", back_populates="robot")