from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.core.config import settings
from app.routes import chat, user, level, home, category, scenario, vocabulary, conversation
from app.api.v1.auth import router as auth_router
from app.core.base_data import init_db

# 1. FastAPI 앱 인스턴스 생성
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 2. CORS 설정 (Flutter 앱이나 웹에서 접근할 수 있도록 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. 순수 SW 라우터 등록
app.include_router(user.router, prefix=f"{settings.API_V1_STR}/users", tags=["Users"])
app.include_router(level.router, prefix=f"{settings.API_V1_STR}/level-test", tags=["Level Test"])
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["Auth"])
app.include_router(home.router, prefix=f"{settings.API_V1_STR}/home", tags=["Home"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["Chat"])
app.include_router(category.router, prefix=f"{settings.API_V1_STR}/category", tags=["Category"])
app.include_router(scenario.router, prefix=f"{settings.API_V1_STR}/scenario", tags=["Scenario"])
app.include_router(conversation.router, prefix=f"{settings.API_V1_STR}/conversation", tags=["Conversation"])
app.include_router(vocabulary.router, prefix=f"{settings.API_V1_STR}/vocabulary", tags=["Vocabulary"])

# 서버 시작 시 실행되는 이벤트 핸들러
@app.on_event("startup")
async def startup_event():
    try:
        Base.metadata.create_all(bind=engine)
        init_db()
        print("[DATABASE] DB 테이블 및 기초 데이터 초기화 성공")
    except Exception as e:
        print(f"[DATABASE WARNING] DB 초기화 중 연결 경고 (배포/테스트 환경 체크 필요): {e}")

@app.get("/")
def root():
    return {
        "message": "Welcome to VIPA API Server",
        "docs": "/docs",
        "version": "1.0.0"
    }
