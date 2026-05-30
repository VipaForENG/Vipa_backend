from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # --- 프로젝트 기본 설정 ---
    PROJECT_NAME: str = "VIPA_BACKEND"
    API_V1_STR: str = "/api/v1"

    # --- 데이터베이스 및 보안 ---
    DATABASE_URL: str = "" 
    SECRET_KEY: str = "YOUR_SUPER_SECRET_KEY"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8



    # 구글/카카오 UserInfo 엔드포인트
    GOOGLE_USERINFO_URL: str = "https://www.googleapis.com/oauth2/v3/userinfo"
    KAKAO_USERINFO_URL: str = "https://kapi.kakao.com/v2/user/me"



    # --- 이메일 설정 (추가됨) ---
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: SecretStr = SecretStr("")
    MAIL_FROM: str = ""
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    # --- 추가된 AI 설정 ---
    OPENAI_API_KEY: str = "" # 필드 정의가 있어야 .env에서 값을 읽어옵니다.

    # --- Payment provider test settings ---
    KAKAO_PAY_API_BASE_URL: str = "https://open-api.kakaopay.com"
    KAKAO_PAY_SECRET_KEY: str = ""
    KAKAO_PAY_CID: str = "TC0ONETIME"
    KAKAO_PAY_SUBSCRIPTION_CID: str = "TCSEQUENCE"

    # --- .env 파일 설정 ---
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore" 
    )

settings = Settings()
