from datetime import datetime
from datetime import timezone

from sqlalchemy.orm import Session
from app.models.user import User
from app.models.robot import RobotControl
from app.schemas.user import UserCreate
from app.core.security import get_password_hash

# 유저 관련 CRUD 함수들
# 이메일 중복 체크 함수
def get_user_by_email(db: Session, email: str):
    """
    이메일로 기존 유저가 있는지 조회합니다. (중복 가입 방지용)
    """
    return db.query(User).filter(User.email == email).first()

# 유저 생성 함수
def create_user(db: Session, user_in: UserCreate):
    """
    새로운 유저를 생성하고, 기본 로봇 설정도 함께 생성합니다.
    """
    # 1. 비밀번호 암호화 (평문 -> 해시)
    hashed_password = get_password_hash(user_in.password)
    
    # 2. 유저 객체 생성
    db_user = User(
        email=user_in.email,
        password=hashed_password,  # 암호화된 비밀번호 저장
        nickname=user_in.nickname,
        is_social=user_in.is_social,
        social_role=user_in.social_role,
        study_count=0  # 초기 스터디 카운트는 0으로 설정
    )
    
    db.add(db_user)
    db.commit()        # DB에 저장
    db.refresh(db_user)   # 생성된 user_id를 객체에 반영
    
    # 3. 유저의 단짝 로봇(RobotControl) 초기 설정 자동 생성
    # 유저가 생길 때 로봇도 같이 태어나야 함. (1:1 관계)
    db_robot = RobotControl(
        user_id=db_user.user_id,      # 생성된 유저 ID 연결 (FK)
        robot_ip=None,                # 초기값은 없음
        is_auto_connect=False,        # 기본값 false
        energy_level=100,             # 초기 에너지 100
        last_sync_at=datetime.now(timezone.utc), # 현재 시간으로 동기화 시작점 설정
        motor_pitch_angle=90,         # 영점 조절 90도
        motor_yaw_angle=90            # 영점 조절 90도
    )
    db.add(db_robot)
    db.commit()
    
    return db_user