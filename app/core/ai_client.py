# app/core/ai_client.py
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
from app.core.config import settings

load_dotenv()

# 비동기 클라이언트 인스턴스
client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY
)

# 모델명 정의 (설정 파일의 모델명 사용)
MODEL_NAME = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")