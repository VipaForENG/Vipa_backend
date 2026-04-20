from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date
from app.core.database import get_db
from app.api import deps
from app.models.user import User
from app.models.level import UserLevel
from app.models.study_log import StudyLog
from app.crud import summary as summary_crud
from app.crud import chat  # 대화 관련 CRUD
from app.utils import gpt5
from app.schemas.chat import ChatRequest, ChatResponse
from typing import cast

router = APIRouter()

@router.post("/talk", response_model=ChatResponse)
async def talking_api(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    # 1. 유저의 최근 CEFR 레벨 조회
    user_level_record = db.query(UserLevel)\
        .filter(UserLevel.user_id == current_user.user_id)\
        .order_by(UserLevel.user_level_id.desc())\
        .first()

    current_cefr: str = user_level_record.cefr_level if user_level_record and user_level_record.cefr_level else "A1"

    # 2. 세션 관리 및 이전 대화 내역(History) 추출
    current_session_id = request.session_id
    history = []

    if current_session_id:
        history = chat.get_recent_messages(db, session_id=current_session_id, limit=5)
    else:
        new_session = chat.create_chat_session(db, user_id=current_user.user_id)
        
        # Pylance에게 이건 무조건 int형이라고 명시
        current_session_id = cast(int, new_session.session_id)
    
    # 3. GPT-5 API 호출 (토큰 사용량 체크 포함)
    today = date.today()
    ai_data = await gpt5.get_chat_response(
        db=db,
        user_id=current_user.user_id,
        user_message=request.user_message,
        history=history,
        cefr_level=current_cefr,
        today=today
    )

    # 4. 토큰 한도 초과 여부 확인
    # gpt5.py에서 한도 초과 시 feedback에 "Limit Reached"를 담기로 약속함
    is_limit = ai_data.get("feedback") == "Limit Reached"
    earned_energy = 0 if is_limit else 5

    if not is_limit:
        # 5. 정상 대화인 경우 DB 기록 업데이트
        
        # A. 대화 문장 로그 저장 (유저 질문 + AI 답변)
        chat.save_chat_turn(
            db=db,
            session_id=current_session_id,
            user_msg=request.user_message,
            ai_en=ai_data.get("en", ""),
            ai_ko=ai_data.get("ko", ""),
            feedback=ai_data.get("feedback", "")
        )

        # B. 학습 로그(StudyLog) 기록
        new_log = StudyLog(
            user_id=current_user.user_id,
            type="CONVERSATION",
            earned_energy=earned_energy
        )
        db.add(new_log)
        
        # C. 일일 요약(Summary) 및 유저 총 학습 횟수 업데이트
        summary_crud.update_daily_summary(
            db, 
            user_id=current_user.user_id, 
            study_type="CONVERSATION", 
            energy=earned_energy
        )
        current_user.study_count += 1 
        
        db.commit()

    # 6. 최종 응답 반환
    return ChatResponse(
        en_content=ai_data.get("en", "Sorry, I couldn't process your request."),
        ko_content=ai_data.get("ko", "죄송합니다. 답변을 생성하지 못했습니다."),
        feedback=ai_data.get("feedback", "N/A"),
        earned_energy=earned_energy,
        is_limit_reached=is_limit
    )