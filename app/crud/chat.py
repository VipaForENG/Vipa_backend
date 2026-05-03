# app/crud/chat.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

# 모델 위치는 실제 경로에 맞게 임포트.
from app.models.conversation_session import ConversationSession
from app.models.sentence_log import SentenceLog

async def create_chat_session(db: AsyncSession, user_id: int, scenario_id: Optional[int] = None) -> ConversationSession:
    """새로운 대화 세션 방을 만듭니다."""
    new_session = ConversationSession(
        user_id=user_id,
        scenario_id=scenario_id # 자유 대화면 None이 들어감
    )
    db.add(new_session)
    # 🚨 [중요] 비동기에서는 하위 함수에서 commit 하지 않습니다. 
    # flush()로 DB에 임시 반영하여 ID값만 뽑아오고, 최종 commit은 라우터가 담당합니다.
    await db.flush() 
    await db.refresh(new_session)
    
    return new_session

async def get_recent_messages(db: AsyncSession, session_id: int, limit: int = 5) -> list:
    """특정 세션의 대화 기록을 가져와 GPT API 포맷에 맞춥니다."""
    # 비동기 select 구문으로 변환
    stmt = select(SentenceLog)\
        .filter(SentenceLog.session_id == session_id)\
        .order_by(SentenceLog.sentencelog_id.desc())\
        .limit(limit)
        
    result = await db.execute(stmt)
    logs = list(result.scalars().all())
    
    # GPT에게 줄 때는 과거 -> 현재 순서여야 하므로 리스트를 뒤집습니다.
    logs.reverse()
    
    history = []
    for log in logs:
        history.append({
            "role": log.role, # 'user' or 'assistant'
            "content": log.original_text # 발화 내용
        })
        
    return history

async def save_chat_turn(db: AsyncSession, session_id: int, user_msg: str, ai_en: str, ai_ko: str, feedback: str, sub_cat_id: Optional[int] = None) -> None:
    """유저의 질문과 AI의 답변을 각각 SentenceLog 테이블에 저장합니다."""
    
    user_log = SentenceLog(
        session_id=session_id,
        sub_cat_id=sub_cat_id,
        role="user",
        original_text=user_msg,
        feedback_comment=feedback 
    )
    
    ai_log = SentenceLog(
        session_id=session_id,
        sub_cat_id=sub_cat_id,
        role="assistant",
        original_text=ai_en,
        translated_text=ai_ko
    )
    
    # 세션 메모리에 객체 등록
    db.add(user_log)
    db.add(ai_log)
    # 🚨 여기 있던 db.commit()은 상위 라우터에서 일괄 처리하므로 제거/flush 처리합니다.
    await db.flush()