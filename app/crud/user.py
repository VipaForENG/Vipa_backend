from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash


def get_user_by_id(db: Session, user_id: int):
    """
    유저 ID(PK)로 유저 정보를 조회합니다.
    """
    return db.query(User).filter(User.user_id == user_id).first()


# --- [조회] 닉네임으로 유저 찾기 ---
def get_user_by_nickname(db: Session, nickname: str):
    """
    닉네임으로 기존 유저가 있는지 조회합니다. (중복 닉네임 방지용)
    """
    return db.query(User).filter(User.nickname == nickname).first()


# --- [조회] 이메일로 유저 찾기 ---
def get_user_by_email(db: Session, email: str):
    """
    이메일로 기존 유저가 있는지 조회합니다. (중복 가입 방지 및 계정 통합용)
    """
    return db.query(User).filter(User.email == email).first()


# --- [생성] 일반 회원가입 ---
def create_user(db: Session, user_in: UserCreate):
    """
    새로운 일반 유저를 생성합니다.
    """
    # 1. 비밀번호 암호화 (평문 -> 해시)
    hashed_password = get_password_hash(user_in.password)
    
    # 2. 유저 객체 생성
    db_user = User(
        email=user_in.email,
        password=hashed_password,
        nickname=user_in.nickname,
        is_social=user_in.is_social,
        social_role=user_in.social_role,
        study_count=0
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


# --- [업데이트] 비밀번호 설정/변경 ---
def set_user_password(db: Session, user_id: int, plain_password: str):
    """
    소셜로 가입했던 유저가 일반 로그인을 위해 비밀번호를 처음 설정하거나 
    기존 비밀번호를 변경할 때 사용합니다.
    """
    db_user = db.query(User).filter(User.user_id == user_id).first()
    if not db_user:
        return None
    
    # 비밀번호 해싱 후 저장
    db_user.password = get_password_hash(plain_password)
    
    db.commit()
    db.refresh(db_user)
    return db_user


# --- 소셜 로그인 처리 (핵심 로직) ---
def process_social_login(db: Session, email: str, nickname: str, provider_bit: int):
    """
    소셜 로그인 시 계정 통합 또는 신규 가입을 처리합니다. (비트마스크 적용)
    - provider_bit: 구글=1, 카카오=2 등
    """
    db_user = get_user_by_email(db, email)
    
    if db_user:
        # 시나리오 A: 기존 유저가 있다면 비트마스크 업데이트 (계정 통합)
        db_user.is_social |= provider_bit
        db.commit()
        db.refresh(db_user)
    else:
        # 시나리오 B: 아예 새로운 소셜 유저라면 가입 처리
        db_user = User(
            email=email,
            nickname=nickname,
            password=None,  # 소셜 유저는 비밀번호가 없음
            is_social=provider_bit,
            social_role=0,
            study_count=0
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
    return db_user


# --- [삭제] 유저 탈퇴 ---
def delete_user(db: Session, user_id: int):
    """
    유저 탈퇴: 유저 데이터를 DB에서 삭제합니다.
    """
    db.query(User).filter(User.user_id == user_id).delete()
    db.commit()
    return True


# --- [업데이트] 유저 프로필 변경 (닉네임, 이미지) ---
def update_user_profile(
    db: Session, 
    user_id: int, 
    nickname: str | None = None, 
    profile_image: str | None = None
):
    """유저의 닉네임과 프로필 이미지를 선택적으로 업데이트합니다."""
    db_user = db.query(User).filter(User.user_id == user_id).first()
    if not db_user:
        return None

    # 값이 전달된 경우에만 덮어쓰기
    if nickname is not None:
        db_user.nickname = nickname
    if profile_image is not None:
        db_user.profile_image = profile_image

    db.commit()
    db.refresh(db_user)
    
    return db_user