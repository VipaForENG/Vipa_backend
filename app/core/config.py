from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # 1. 필드 선언 (기본값을 None으로 주거나 생략해도 되지만, 
    # Pylance 에러를 피하려면 Optional이나 기본값을 명시하는게 좋음.)
    PROJECT_NAME: str = "VIPA_BACKEND"
    API_V1_STR: str = "/api/v1"
    
    # Optional을 사용하거나 빈 문자열을 기본값으로 줍니다.
    DATABASE_URL: str = "" 
    
    SECRET_KEY: str = "YOUR_SUPER_SECRET_KEY"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8

    # 2. .env 파일 설정
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore" # .env에 클래스 정의 외의 값이 있어도 무시함
    )

# 이제 인자 없이 호출해도 에러가 나지 않습니다.
settings = Settings()