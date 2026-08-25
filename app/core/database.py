import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings

# --- [동기(Sync) 및 비동기(Async) DB URL 안전 구성] ---
raw_url = settings.DATABASE_URL.strip() if settings.DATABASE_URL else ""

# SQLite 로컬 데이터베이스를 기본 안전 Fallback으로 사용
LOCAL_SQLITE_URL = "sqlite:///./vipa_local.db"
LOCAL_ASYNC_SQLITE_URL = "sqlite+aiosqlite:///./vipa_local.db"

# 테스트 환경이거나 URL이 유효하지 않으면 SQLite 사용
use_sqlite = os.getenv("VIPA_USE_SQLITE", "false").lower() == "true" or not raw_url

if use_sqlite:
    SQLALCHEMY_DATABASE_URL = LOCAL_SQLITE_URL
    ASYNC_DATABASE_URL = LOCAL_ASYNC_SQLITE_URL
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    SQLALCHEMY_DATABASE_URL = raw_url
    ASYNC_DATABASE_URL = raw_url.replace("postgresql://", "postgresql+asyncpg://")
    try:
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        # 빠른 연결 테스트
        with engine.connect() as conn:
            pass
    except Exception as e:
        print(f"[DB WARNING] 원격 DB 접속 실패 ({e}), 로컬 SQLite로 자동 전환합니다.")
        SQLALCHEMY_DATABASE_URL = LOCAL_SQLITE_URL
        ASYNC_DATABASE_URL = LOCAL_ASYNC_SQLITE_URL
        engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

try:
    async_engine = create_async_engine(ASYNC_DATABASE_URL)
except Exception:
    async_engine = create_async_engine(LOCAL_ASYNC_SQLITE_URL)

AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session