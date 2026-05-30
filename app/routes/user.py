
import os
import uuid
import shutil
from datetime import datetime, timedelta, timezone
import secrets
from typing import cast, Any

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from fastapi_mail import MessageSchema, MessageType

from app.core.database import get_db
from app.core import security
from app.core.mail import fastmail
from app.crud import user as user_crud
from app.schemas.user import (
    Msg, VerifyRecoveryCode, PasswordRecoveryEmail, 
    UserCreate, UserLogin, UserResponse, Token, ResetPassword, PasswordChangeRequest
)
from app.crud import level as level_crud
from app.core.security import get_current_user_id
router = APIRouter()
from app.core.storage import SupabaseStorageService 
from app.models.user import User


from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

# --- [유저 기본 기능] ---

@router.get("/me", response_model=UserResponse)
def read_user_me(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id) # JWT 토큰 검증 완료
):
    """
    내 정보 조회 API:
    JWT 토큰을 통해 인증된 유저의 상세 정보를 반환합니다.
    """
    # 1. DB에서 유저 조회
    user = user_crud.get_user_by_id(db, user_id=user_id)
    
    # 2. 유저가 없는 경우(DB 삭제 등)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="사용자를 찾을 수 없습니다."
        )
    
    # 3. 유저 정보 반환 (UserResponse 스키마에 따라 필요한 필드들이 나갑니다)
    return user


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    회원가입 API: 이메일과 닉네임을 각각 검증하여 정확한 에러 메시지를 제공합니다.
    """
    # 1. 이메일 중복 존재 확인
    if user_crud.get_user_by_email(db, email=user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 사용 중인 이메일입니다."
        )
    
    # 2. 닉네임 중복 존재 확인 (이제 Pylance 에러가 사라집니다)
    if user_crud.get_user_by_nickname(db, nickname=user_in.nickname):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 사용 중인 닉네임입니다."
        )
    
    # 3. 데이터베이스 저장 및 예외 처리
    try:
        new_user = user_crud.create_user(db=db, user_in=user_in)
        return new_user
    except IntegrityError:
        db.rollback()
        # 존재 검사를 했음에도 동시성 이슈로 에러가 날 경우를 대비한 최후의 방어선
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 이메일 또는 닉네임입니다."
        )


@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    """
    로그인 API: 이메일과 비밀번호 검증 후 JWT 액세스 토큰을 발급합니다.
    """
    db_user = user_crud.get_user_by_email(db, email=user_in.email)
    
    # DB에 저장된 hashed_password와 입력된 plain_password 비교
    # Pylance 타입 에러 방지를 위해 cast(str, ...) 사용
    if not db_user or not security.verify_password(user_in.password, cast(str, db_user.password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 일치하지 않습니다."
        )

    # 레벨 테스트 기록이 있는지 확인
    # level_crud에 유저의 레벨 정보를 가져오는 함수가 있다고 가정합니다.
    user_level = level_crud.get_user_level(db, user_id=db_user.user_id)
    is_tested = True if user_level else False

    # 유저 ID를 기반으로 액세스 토큰 생성
    access_token = security.create_access_token(subject=db_user.user_id)
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "is_tested": is_tested 
    }


# --- [비밀번호 찾기 프로세스] ---

@router.post("/password-recovery/send-code", response_model=Msg)
async def send_recovery_code(
    email_in: PasswordRecoveryEmail, 
    db: Session = Depends(get_db)
):
    """
    1 단계 - 코드 발송: 이메일 존재 확인 후 6자리 인증 코드를 메일로 보냄
    """
    user = user_crud.get_user_by_email(db, email=email_in.email)
    if not user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")

    # 1. 6자리 랜덤 숫자 생성
    reset_code = f"{secrets.randbelow(1000000):06d}"
    
    # 2. DB 유저 객체에 코드와 만료시간(10분) 기록
    user.reset_code = reset_code
    user.reset_code_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.commit()

    # 3. 이메일 메시지 구성 (Pylance recipients 에러 방지를 위해 cast 사용)
    message = MessageSchema(
        subject="[VIPA] 비밀번호 재설정 인증 코드",
        recipients=cast(Any, [str(user.email)]), 
        body=f"인증 코드: [{reset_code}]\n10분 이내에 입력해 주세요.",
        subtype=MessageType.plain
    )

    # 4. fastmail 인스턴스를 통한 비동기 메일 발송
    await fastmail.send_message(message)
    
    return {"message": "인증 코드가 이메일로 발송되었습니다."}


@router.post("/password-recovery/verify-code", response_model=Msg)
def verify_recovery_code(verify_in: VerifyRecoveryCode, db: Session = Depends(get_db)):
    """
    2 단계 - 코드 검증: 입력한 코드가 DB의 코드와 일치하는지, 만료되지 않았는지 확인.
    """
    user = user_crud.get_user_by_email(db, email=verify_in.email)
    if not user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")

    # 1. 코드 일치 여부 검사 (SQLAlchemy Column 비교 에러 방지를 위해 cast)
    if not cast(bool, user.reset_code == verify_in.code):
        raise HTTPException(status_code=400, detail="인증 코드가 일치하지 않습니다.")

    # 2. 시간 만료 여부 검사
    now = datetime.now(timezone.utc)
    if user.reset_code_expires_at and now > user.reset_code_expires_at:
        raise HTTPException(status_code=400, detail="인증 코드가 만료되었습니다.")

    return {"message": "인증에 성공했습니다. 새로운 비밀번호로 변경해 주세요."}


@router.patch("/password-recovery/reset", response_model=Msg)
def reset_password(reset_in: ResetPassword, db: Session = Depends(get_db)):
    """
    3 단계 - 비밀번호 변경: 인증된 정보를 바탕으로 새로운 비밀번호를 해싱하여 저장함.
    """
    user = user_crud.get_user_by_email(db, email=reset_in.email)
    if not user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")

    # 1. 보안을 위한 재검증(코드 일치 및 시간 확인)
    if not cast(bool, user.reset_code == reset_in.code):
        raise HTTPException(status_code=400, detail="유효하지 않은 인증 코드입니다.")
    
    now = datetime.now(timezone.utc)
    if user.reset_code_expires_at and now > user.reset_code_expires_at:
        raise HTTPException(status_code=400, detail="인증 시간을 초과했습니다.")

    # 2. 새로운 비밀번호 해싱 및 업데이트
    user.password = cast(Any, security.get_password_hash(reset_in.new_password))
    
    # 3. 사용 완료된 인증 코드 초기화(보안상 필수)
    user.reset_code = None
    user.reset_code_expires_at = None
    
    db.commit()

    return {"message": "비밀번호가 성공적으로 변경되었습니다."}


# -- 비밀번호 재설정 (인증된 유저) ---

@router.patch("/mypage/change-password")
def change_password(
    data: PasswordChangeRequest, 
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id) # 이미 위에서 정의되어 있음
):
    # 1. DB에서 유저 조회 (db_user가 None일 수 있음을 인지)
    db_user = db.query(User).filter(User.user_id == user_id).first()
    
    # 2. 유저가 없을 경우 Null 체크 (Pylance 에러 해결)
    if not db_user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
    
    # 3. 기존 비밀번호 검증(db_user.password가 None일 경우를 대비해 str()로 캐스팅)
    if not security.verify_password(data.old_password, str(db_user.password)):
        raise HTTPException(status_code=400, detail="기존 비밀번호가 일치하지 않습니다.")
    
    # 4. 새로운 비밀번호 해싱 및 저장
    db_user.password = security.get_password_hash(data.new_password)
    db.commit()
    
    return {"message": "비밀번호가 변경되었습니다."}


# --- [회원 탈퇴] ---

@router.delete("/withdraw", response_model=Msg)
def withdraw_user(
    db: Session = Depends(get_db),
    # 1. 여기서 토큰을 검증하고 user_id를 바로 추출합니다.
    user_id: int = Depends(get_current_user_id) 
):
    """
    회원 탈퇴 API:
    JWT 토큰에서 추출한 user_id를 사용하여 계정을 삭제합니다.
    """
    try:
        # 2. 추출한 user_id를 삭제 로직에 전달
        user_crud.delete_user(db=db, user_id=user_id)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="회원 탈퇴 처리 중 오류가 발생했습니다."
        )
    
    return {"message": "계정이 성공적으로 삭제되었습니다."}

# --- [프로필 업데이트] ---

# 의존성 주입을 위한 인스턴스 생성 헬퍼
def get_storage_service():
    return SupabaseStorageService()

@router.patch("/me/profile", response_model=UserResponse)
async def update_my_profile(
    nickname: str | None = Form(None),
    profile_image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    [API] 프로필(닉네임 및 이미지) 수정 엔드포인트
    - 기능: 유저 검증, 닉네임 중복 체크를 수행한 후 이미지가 존재하면 Supabase Cloud 스토리지에 저장하고 그 URL을 DB에 기록합니다.
    """
    # 1. 대상 유저 검증
    current_user = user_crud.get_user_by_id(db, user_id=user_id)
    if not current_user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")

    # 2. 닉네임 변경 시 중복 검사
    if nickname and nickname != current_user.nickname:
        existing_user = user_crud.get_user_by_nickname(db, nickname=nickname)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="이미 사용 중인 닉네임입니다."
            )

    # 3. 이미지 업로드 로직 수행
    image_url = current_user.profile_image
    if profile_image:
        try:
            storage_service = get_storage_service()
            # 로컬 디스크가 아닌 Supabase Storage로 직접 업로드하고 스토리지 주소(https://...)를 받아옵니다.
            image_url = await storage_service.save_file(profile_image, folder="avatar")
        except RuntimeError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    # 4. 데이터베이스 트랜잭션 갱신
    try:
        updated_user = user_crud.update_user_profile(
            db=db, 
            user_id=user_id, 
            nickname=nickname, 
            profile_image=image_url
        )
        return updated_user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="데이터베이스 갱신 중 오류가 발생했습니다."
        )