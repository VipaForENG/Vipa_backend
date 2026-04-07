from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # --- 프로젝트 기본 설정 ---
    PROJECT_NAME: str = "VIPA_BACKEND"
    API_V1_STR: str = "/api/v1"

    # https://localhost:8000/api/v1/users/login

    # --- 데이터베이스 및 보안 ---
    DATABASE_URL: str = "" 
    SECRET_KEY: str = "YOUR_SUPER_SECRET_KEY"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8

    # --- 이메일 설정 (추가됨) ---
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: SecretStr = SecretStr("")
    MAIL_FROM: str = ""
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    # --- .env 파일 설정 ---
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore" 
    )

settings = Settings()