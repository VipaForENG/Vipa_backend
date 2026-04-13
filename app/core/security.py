from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union
from jose import jwt, JWTError # 🔥 JWTError 추가
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer # 🔥 토큰 추출기 추가
from app.core.config import settings

# bcrypt 알고리즘을 사용하도록 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 헤더에서 "Bearer <토큰>"을 자동으로 추출하는 FastAPI 도구 
# (tokenUrl은 Swagger UI에서 테스트할 때 로그인 API의 경로를 의미합니다)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/users/login")


# --- 비밀번호 해싱과 검증 함수 ---
def get_password_hash(password: str) -> str:
    """사용자가 입력한 평문 비밀번호를 해시(암호문)로 변환합니다."""
    password_bytes = password.encode('utf-8')
    safe_password_bytes = password_bytes[:72]
    return pwd_context.hash(safe_password_bytes)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """평문 비밀번호와 DB에 저장된 해시 값을 비교합니다."""
    plain_password_bytes = plain_password.encode('utf-8')
    safe_plain_password_bytes = plain_password_bytes[:72]
    return pwd_context.verify(safe_plain_password_bytes, hashed_password)

# --- 토큰 생성 로직 ---
def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """로그인 성공 시 앱에 전달할 JWT 토큰을 생성합니다."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt 


# ==========================================
# 토큰 검증 및 유저 ID 추출 보초병
# ==========================================
def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    """
    API 요청 헤더에 포함된 JWT 토큰을 해독하여 사용자 ID(user_id)를 반환합니다.
    토큰이 조작되었거나 만료된 경우 401 에러를 발생시킵니다.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="토큰이 유효하지 않거나 만료되었습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 1. 토큰 해독 (설정된 SECRET_KEY 사용)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # 2. 토큰 생성 시 넣었던 "sub" (subject) 값 추출
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        # 3. DB PK 타입에 맞춰 int로 변환하여 반환
        return int(user_id)
        
    except JWTError:
        raise credentials_exception
    except ValueError:
        raise credentials_exception