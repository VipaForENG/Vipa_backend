from datetime import datetime, timedelta, timezone
import secrets
from typing import cast, List, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi_mail import MessageSchema, MessageType

from app.core.database import get_db
from app.core import security
from app.core.mail import fastmail
from app.crud import user as user_crud
from app.schemas.user import (
    Msg, VerifyRecoveryCode, PasswordRecoveryEmail, 
    UserCreate, UserLogin, UserResponse, Token, ResetPassword
)

router = APIRouter()

# --- [유저 기본 기능] ---

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    회원가입 API: 이메일 중복 확인 후 유저와 기본 로봇 데이터를 함께 생성합니다.
    """
    # 1. 이미 가입된 이메일인지 중복 확인
    db_user = user_crud.get_user_by_email(db, email=user_in.email)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="이미 존재하는 이메일입니다."
        )
    
    # 2. CRUD 로직을 통해 유저+로봇 생성 (비밀번호 해싱은 CRUD 내부에서 처리됨)
    new_user = user_crud.create_user(db=db, user_in=user_in)
    return new_user


@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    """
    로그인 API: 이메일/비밀번호 검증 후 JWT 액세스 토큰을 발급합니다.
    """
    db_user = user_crud.get_user_by_email(db, email=user_in.email)
    
    # DB에 저장된 hashed_password와 입력된 plain_password 비교
    # Pylance 타입 에러 방지를 위해 cast(str, ...) 사용
    if not db_user or not security.verify_password(user_in.password, cast(str, db_user.password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 일치하지 않습니다."
        )

    # 유저 ID를 기반으로 액세스 토큰 생성
    access_token = security.create_access_token(subject=db_user.user_id)
    return {"access_token": access_token, "token_type": "bearer"}


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
    2 단계 - 코드 검증: 입력된 코드가 DB의 코드와 일치하는지, 만료되지는 않았는지 확인함.
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

    # 1. 보안을 위한 재검증 (코드 일치 및 시간 확인)
    if not cast(bool, user.reset_code == reset_in.code):
        raise HTTPException(status_code=400, detail="유효하지 않은 인증 코드입니다.")
    
    now = datetime.now(timezone.utc)
    if user.reset_code_expires_at and now > user.reset_code_expires_at:
        raise HTTPException(status_code=400, detail="인증 시간이 초과되었습니다.")

    # 2. 새로운 비밀번호 해싱 및 업데이트
    user.password = cast(Any, security.get_password_hash(reset_in.new_password))
    
    # 3. 사용 완료된 인증 코드 초기화 (보안상 필수)
    user.reset_code = None
    user.reset_code_expires_at = None
    
    db.commit()

    return {"message": "비밀번호가 성공적으로 변경되었습니다."}