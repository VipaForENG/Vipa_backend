# user 테이블 모델 정의한것. 
from sqlalchemy import Column, Integer, String, SmallInteger
from sqlalchemy.orm import relationship
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

    # 관계 설정 (로봇 설정과 1:1 연결)
    robot = relationship("RobotControl", back_populates="owner", uselist=False, cascade="all, delete-orphan")