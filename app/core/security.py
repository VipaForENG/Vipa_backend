from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union
from jose import jwt # 나중에 토큰 발행 시 필요
from app.core.config import settings

# bcrypt 알고리즘을 사용하도록 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- 비밀번호 해싱과 검증 함수 ---
def get_password_hash(password: str) -> str:
    """
    사용자가 입력한 평문 비밀번호를 해시(암호문)로 변환합니다.
    회원가입 시 사용합니다.
    """
    password_bytes = password.encode('utf-8')
    safe_password_bytes = password_bytes[:72]
    return pwd_context.hash(safe_password_bytes)

# 로그인 시 입력한 비밀번호와 DB에 저장된 해시 값을 비교하는 함수임.
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    평문 비밀번호와 DB에 저장된 해시 값을 비교합니다.
    로그인 시 사용합니다.
    """
    plain_password_bytes = plain_password.encode('utf-8')
    safe_plain_password_bytes = plain_password_bytes[:72]
    return pwd_context.verify(safe_plain_password_bytes, hashed_password)

# --- 나중에 로그인 기능을 위해 미리 넣어두는 토큰 생성 로직 ---
def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    로그인 성공 시 앱에 전달할 JWT 토큰을 생성합니다.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt