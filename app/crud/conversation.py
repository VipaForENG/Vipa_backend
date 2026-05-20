from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Tuple

from app.models.conversation_session import ConversationSession
from app.models.study_log import StudyLog
# 💡 아래 두 개는 파트너님의 실제 모델에 맞게 임포트 하세요!
from app.models.custom_scenario import CustomScenario 
from app.models.sentence_log import SentenceLog # AI 교정 노트용 모델 임포트
from app.models.category import SubCategory


# ---------------------------------------------------------
# [참고] 대시보드 API에서 호출하는 실제 쿼리 함수
# ---------------------------------------------------------
def get_conversation_history_dashboard(db: Session, user_id: int):
    """
    실전 회화 통합 대시보드 데이터 조회 (최종 완성 버전)
    """
    
    # 1. [최근 세션]
    recent_query = db.query(ConversationSession, CustomScenario, SubCategory).outerjoin(
        CustomScenario, ConversationSession.scenario_id == CustomScenario.scenario_id
    ).outerjoin(
        SubCategory, CustomScenario.sub_cat_id == SubCategory.sub_cat_id
    ).filter(
        ConversationSession.user_id == user_id
    ).order_by(desc(ConversationSession.created_at)).limit(3).all()

    recent_sessions = []
    for session, scenario, sub_cat in recent_query:
        # JSON 데이터에서 제목 추출
        title = scenario.generated_script.get("title", f"시나리오 #{scenario.scenario_id}") if scenario else "자유 대화"
        # 🌟 'name' -> 'sub_title'로 수정
        category = sub_cat.sub_title if sub_cat else "Free" 
        
        recent_sessions.append({
            "session_id": session.session_id,
            "scenario_title": title,
            "category": category,
            "created_at": session.created_at,
            "audio_url": session.audio_url
        })

    # 2. [AI 교정 리스트]
    raw_corrections = db.query(SentenceLog).join(
        ConversationSession, SentenceLog.session_id == ConversationSession.session_id
    ).filter(
        ConversationSession.user_id == user_id,
        SentenceLog.role == "user",
        SentenceLog.corrected_text.is_not(None)
    ).order_by(desc(SentenceLog.created_at)).limit(5).all()

    # 🌟 핵심: 모델 객체를 Pydantic 스키마가 원하는 필드명으로 변환
    ai_corrections = [
        {
            "turn_id": log.sentencelog_id,
            "session_id": log.session_id,
            "user_input": log.original_text,
            "corrected_en": log.corrected_text,
            "feedback_ko": log.feedback_comment
        }
        for log in raw_corrections
    ]

    # 3. [카테고리 현황] SubCategory.sub_title 기준으로 그룹화
    progress_query = db.query(
        SubCategory.sub_title,
        func.count(StudyLog.session_id).label("completed_count")
    ).join(
        ConversationSession, StudyLog.session_id == ConversationSession.session_id
    ).join(
        CustomScenario, ConversationSession.scenario_id == CustomScenario.scenario_id
    ).join(
        SubCategory, CustomScenario.sub_cat_id == SubCategory.sub_cat_id
    ).filter(
        StudyLog.user_id == user_id,
        StudyLog.type == 'CONVERSATION'
    ).group_by(SubCategory.sub_title).all()

    # 🌟 결과 리스트 조립 시에도 sub_title 사용
    category_progress = [
        {"category": title, "completed_sessions": count}
        for title, count in progress_query
    ]

    return recent_sessions, ai_corrections, category_progress