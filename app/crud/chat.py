from sqlalchemy.orm import Session

from typing import Optional

# 모델 위치는 실제 경로에 맞게 임포트.
from app.models.conversation_session import ConversationSession
from app.models.sentence_log import SentenceLog

def create_chat_session(db: Session, user_id: int, scenario_id: Optional[int] = None) -> ConversationSession:
    """새로운 대화 세션 방을 만듭니다."""
    new_session = ConversationSession(
        user_id=user_id,
        scenario_id=scenario_id # 자유 대화면 None이 들어감
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return new_session

def get_recent_messages(db: Session, session_id: int, limit: int = 5) -> list:
    """특정 세션의 대화 기록을 가져와 GPT API 포맷에 맞춥니다."""
    # sentencelog_id (또는 created_at) 역순으로 최신 대화 조회
    logs = db.query(SentenceLog)\
        .filter(SentenceLog.session_id == session_id)\
        .order_by(SentenceLog.sentencelog_id.desc())\
        .limit(limit)\
        .all()
    
    # GPT에게 줄 때는 과거 -> 현재 순서여야 하므로 리스트를 뒤집습니다.
    logs.reverse()
    
    history = []
    for log in logs:
        history.append({
            "role": log.role, # 'user' or 'assistant'
            "content": log.original_text # 발화 내용
        })
        
    return history

def save_chat_turn(db: Session, session_id: int, user_msg: str, ai_en: str, ai_ko: str, feedback: str, sub_cat_id: Optional[int] = None) -> None:
    """유저의 질문과 AI의 답변을 각각 SentenceLog 테이블에 저장합니다."""
    
    # 1. 유저의 발화 기록
    user_log = SentenceLog(
        session_id=session_id,
        sub_cat_id=sub_cat_id,
        role="user",
        original_text=user_msg,
        # 유저가 말한 것에 대한 피드백이므로 유저 로그에 저장하는 것이 구조상 깔끔합니다.
        feedback_comment=feedback 
    )
    
    # 2. AI의 답변 기록
    ai_log = SentenceLog(
        session_id=session_id,
        sub_cat_id=sub_cat_id,
        role="assistant",
        original_text=ai_en,
        translated_text=ai_ko
    )
    
    # 한 번의 트랜잭션으로 저장
    db.add(user_log)
    db.add(ai_log)
    db.commit()