from typing import Optional
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer  # 명칭 확인
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User


# fastapi.security.reusable_oauth2는 존재하지 않음. 직접 정의해야 함.
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login" 
)

def get_current_user(
    db: Session = Depends(get_db), 
    token: str = Depends(reusable_oauth2)
) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # 수정 포인트: user_id의 타입을 Optional로 받고 None 체크를 합니다.
        user_id: Optional[str] = payload.get("sub") 
        if user_id is None:
            raise HTTPException(status_code=401, detail="토큰에 유저 정보가 없음")
            
    except (JWTError, ValidationError):
        raise HTTPException(status_code=403, detail="인증 정보가 유효하지 않음")
        
    # user_id는 이제 확실히 str이므로 int로 변환 가능
    user = db.query(User).filter(User.user_id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없음")
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    # 유저의 상태를 체크하는 로직 (예: 탈퇴 여부, 정지 여부 등)
    # 현재는 활성화된 유저만 반환하도록 간단히 구성
    if not current_user:
        raise HTTPException(status_code=400, detail="비활성화된 유저입니다.")
    return current_user