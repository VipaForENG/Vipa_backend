# app/api/v1/auth.py

from app.crud import level as level_crud


from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token
from app.core.constants import SOCIAL_GOOGLE, SOCIAL_KAKAO
from app.utils.social_auth import get_google_user_info, get_kakao_user_info
from app.crud import user as user_crud
from app.schemas.user import Token, SocialLoginRequest # 스키마 임포트

router = APIRouter()

@router.post("/login/google", response_model=Token)
async def login_google(
    request: SocialLoginRequest, 
    db: Session = Depends(get_db)
):
    """
    구글 소셜 로그인:
    - 액세스 토큰을 검증하고, 이메일이 같으면 계정을 자동 통합(Bitmask)합니다.
    """
    # 1. 구글 유저 정보 확인
    social_info = await get_google_user_info(request.access_token)
    
    # 2. 통합 로직 실행 (비트 1 적용: SOCIAL_GOOGLE)
    user = user_crud.process_social_login(
        db, 
        email=social_info["email"], 
        nickname=social_info["nickname"], 
        provider_bit=SOCIAL_GOOGLE
    )
    user_level = level_crud.get_user_level(db, user_id=user.user_id)
    is_tested = True if user_level else False

    # 3. VIPA 전용 JWT 발행
    return {
        "access_token": create_access_token(user.user_id), 
        "token_type": "bearer",
        "is_tested": is_tested
    }

@router.post("/login/kakao", response_model=Token)
async def login_kakao(
    request: SocialLoginRequest, 
    db: Session = Depends(get_db)
):
    """
    카카오 소셜 로그인:
    - 액세스 토큰을 검증하고, 이메일이 같으면 계정을 자동 통합(Bitmask)합니다.
    """
    # 1. 카카오 유저 정보 확인
    social_info = await get_kakao_user_info(request.access_token)
    
    # 2. 통합 로직 실행 (비트 2 적용: SOCIAL_KAKAO)
    user = user_crud.process_social_login(
        db, 
        email=social_info["email"], 
        nickname=social_info["nickname"], 
        provider_bit=SOCIAL_KAKAO
    )
    
    # 3. VIPA 전용 JWT 발행
    return {
        "access_token": create_access_token(user.user_id), 
        "token_type": "bearer",
        "is_tested": is_tested
    }