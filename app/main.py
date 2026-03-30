from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.core.config import settings
from app.routes import user

# 1. DB 테이블 생성 (앱 실행 시 모델에 정의된 테이블이 없으면 자동 생성)
# 주의: 이미 테이블이 있다면 아무 작업도 하지 않습니다.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 2. CORS 설정 (Flutter 앱이나 웹에서 접근할 수 있도록 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 배포 환경에서 특정 도메인만 허용할 예정.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. 라우터 등록
# prefix를 "/api/v1/users"로 잡으면, signup 함수는 "/api/v1/users/signup"이 됩니다.
app.include_router(user.router, prefix=f"{settings.API_V1_STR}/users", tags=["Users"])

@app.get("/")
def root():
    return {
        "message": "Welcome to VIPA API Server",
        "docs": "/docs",
        "version": "1.0.0"
    }