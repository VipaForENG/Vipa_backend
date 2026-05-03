from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date
from typing import cast

from app.core.database import get_async_db
from app.api import deps
from app.models.user import User
from app.models.level import UserLevel
from app.models.study_log import StudyLog
from app.crud.daily_summary import daily_summary_crud as summary_crud
from app.crud import chat  # 대화 관련 CRUD (이 부분도 비동기로 변경되어야 함)
from app.utils import gpt5
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()

@router.post("/talk", response_model=ChatResponse)
async def talking_api(
    request: ChatRequest,
    db: AsyncSession = Depends(get_async_db), # [핵심 변경] AsyncSession 주입
    current_user: User = Depends(deps.get_current_active_user)
):
    # 1. 유저의 최근 CEFR 레벨 조회 (비동기 변환)
    level_stmt = select(UserLevel)\
        .filter(UserLevel.user_id == current_user.user_id)\
        .order_by(UserLevel.user_level_id.desc())
    user_level_record = (await db.execute(level_stmt)).scalars().first()

    current_cefr: str = user_level_record.cefr_level if user_level_record and user_level_record.cefr_level else "A1"

    # 2. 세션 관리 및 이전 대화 내역 추출 (비동기 함수로 호출)
    current_session_id = request.session_id
    history = []

    if current_session_id:
        # 주의: crud/chat.py 내부의 get_recent_messages도 async 함수여야 함
        history = await chat.get_recent_messages(db, session_id=current_session_id, limit=5)
    else:
        # 주의: create_chat_session도 async 함수여야 함
        new_session = await chat.create_chat_session(db, user_id=current_user.user_id)
        current_session_id = cast(int, new_session.session_id)
    
    # 3. GPT-5 API 호출
    today = date.today()
    ai_data = await gpt5.get_chat_response(
        db=db,
        user_id=current_user.user_id,
        user_message=request.user_message,
        history=history,
        cefr_level=current_cefr,
        today=today
    )

    # 4. 토큰 한도 확인
    is_limit = ai_data.get("feedback") == "Limit Reached"
    earned_energy = 0 if is_limit else 5

    if not is_limit:
        # 5. 정상 대화 기록 (비동기 전환)
        
        # A. 대화 문장 로그 저장
        await chat.save_chat_turn(
            db=db,
            session_id=current_session_id,
            user_msg=request.user_message,
            ai_en=ai_data.get("en", ""),
            ai_ko=ai_data.get("ko", ""),
            feedback=ai_data.get("feedback", "")
        )

        # B. 학습 로그(StudyLog) 기록 (동기 add 후 비동기 flush)
        new_log = StudyLog(
            user_id=current_user.user_id,
            type="CONVERSATION",
            earned_energy=earned_energy
        )
        db.add(new_log)
        
        # C. 일일 요약 및 에너지 업데이트 (방금 만든 비동기 모듈)
        await summary_crud.update_daily_energy(
            db, 
            user_id=current_user.user_id, 
            study_type="CONVERSATION", 
            energy=earned_energy
        )
        current_user.study_count += 1 
        
        # D. 모든 트랜잭션을 한 번에 비동기 커밋
        await db.commit()

    # 6. 최종 응답
    return ChatResponse(
        en_content=ai_data.get("en", "Sorry, I couldn't process your request."),
        ko_content=ai_data.get("ko", "죄송합니다. 답변을 생성하지 못했습니다."),
        feedback=ai_data.get("feedback", "N/A"),
        earned_energy=earned_energy,
        is_limit_reached=is_limit
    )