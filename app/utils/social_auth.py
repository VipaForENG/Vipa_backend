import httpx
import logging
from fastapi import HTTPException, status
from app.core.config import settings

# 로그 설정 (서버 터미널에서 에러 원인을 빠르게 파악하기 위함)
logger = logging.getLogger(__name__)

async def get_google_user_info(access_token: str) -> dict:
    """
    Google 액세스 토큰을 사용하여 유저 정보를 가져옵니다.
    - Endpoint: https://www.googleapis.com/oauth2/v3/userinfo
    - 필요 Scope: email, profile
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    
    async with httpx.AsyncClient() as client:
        try:
            # 1. 구글 서버에 유저 정보 요청
            response = await client.get(settings.GOOGLE_USERINFO_URL, headers=headers)
            
            # 2. 응답 코드가 200이 아닐 경우 처리
            if response.status_code != 200:
                logger.error(f"Google API Error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, 
                    detail="유효하지 않은 구글 토큰이거나 인증이 만료되었습니다."
                )
            
            data = response.json()
            
            # 3. 필수 데이터(이메일) 존재 여부 확인
            email = data.get("email")
            if not email:
                raise HTTPException(status_code=400, detail="구글 계정에 등록된 이메일 정보를 찾을 수 없습니다.")

            # 4. VIPA 백엔드 규격에 맞춰 데이터 반환
            return {
                "email": email,
                "nickname": data.get("name", "Google User"), # 이름이 없을 경우 기본값 설정
                "social_id": data.get("sub") # 구글의 고유 식별자
            }
            
        except httpx.RequestError as exc:
            # 네트워크 연결 오류 처리
            logger.error(f"Google Connection Error: {exc}")
            raise HTTPException(status_code=503, detail="구글 인증 서버에 연결할 수 없습니다.")

async def get_kakao_user_info(access_token: str) -> dict:
    """
    Kakao 액세스 토큰을 사용하여 유저 정보를 가져옵니다.
    - Endpoint: https://kapi.kakao.com/v2/user/me
    - 필수 설정: 카카오 디벨로퍼스 내 '카카오계정(이메일)' 동의 항목 활성화 필요
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-type": "application/x-www-form-urlencoded;charset=utf-8"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # 1. 카카오 서버에 유저 정보 요청
            response = await client.get(settings.KAKAO_USERINFO_URL, headers=headers)
            
            # 2. 응답 코드가 200이 아닐 경우 처리
            if response.status_code != 200:
                logger.error(f"Kakao API Error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, 
                    detail="유효하지 않은 카카오 토큰이거나 인증이 만료되었습니다."
                )
            
            data = response.json()
            kakao_account = data.get("kakao_account", {})
            profile = kakao_account.get("profile", {})
            
            # 3. 이메일 권한 체크 (사용자가 이메일 제공을 거부했을 경우 대비)
            email = kakao_account.get("email")
            if not email:
                # 이메일이 없으면 우리 서비스의 계정 통합 로직이 불가능하므로 에러 발생
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="카카오 이메일 제공 동의가 반드시 필요합니다."
                )

            # 4. VIPA 백엔드 규격에 맞춰 데이터 반환
            return {
                "email": email,
                "nickname": profile.get("nickname", "Kakao User"),
                "social_id": str(data.get("id")) # 카카오 고유 ID (숫자이므로 문자열로 변환)
            }

        except httpx.RequestError as exc:
            # 네트워크 연결 오류 처리
            logger.error(f"Kakao Connection Error: {exc}")
            raise HTTPException(status_code=503, detail="카카오 인증 서버에 연결할 수 없습니다.")