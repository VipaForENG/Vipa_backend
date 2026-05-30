from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException
import json

from app.models.conversation_session import ConversationSession
from app.models.custom_scenario import CustomScenario 
from app.models.sentence_log import SentenceLog
from app.models.category import SubCategory
from app.models.conversation_session import ConversationSession
from app.models.custom_scenario import CustomScenario
from app.models.sentence_log import SentenceLog
from app.models.study_log import StudyLog


def _extract_scenario_title(scenario: CustomScenario | None) -> str:
    if scenario is None:
        return "자유 대화"

    script_data = scenario.generated_script
    if isinstance(script_data, str):
        try:
            script_data = json.loads(script_data)
        except json.JSONDecodeError:
            script_data = {}

    if isinstance(script_data, dict):
        return script_data.get("title", f"시나리오 #{scenario.scenario_id}")

    return f"시나리오 #{scenario.scenario_id}"

# 1. 학습 내역 리스트 조회 (통계 제거, 심플하게 리스트만 반환)
def get_conversation_history_list(db: Session, user_id: int):
    query = db.query(ConversationSession, CustomScenario, SubCategory).outerjoin(
        CustomScenario, ConversationSession.scenario_id == CustomScenario.scenario_id
    ).outerjoin(
        SubCategory, CustomScenario.sub_cat_id == SubCategory.sub_cat_id
    ).filter(
        ConversationSession.user_id == user_id
    ).order_by(desc(ConversationSession.created_at)).limit(20).all()

    recent_sessions = []
    for session, scenario, sub_cat in query:
        # ✨ 수정: generated_script가 안전한 dict 형태인지 확인 후 안전하게 제목 추출
        title = "자유 대화"
        if scenario and isinstance(scenario.generated_script, dict):
            title = scenario.generated_script.get("title", f"시나리오 #{scenario.scenario_id}")

        category = sub_cat.sub_title if sub_cat else "Free" 
        
        recent_sessions.append({
            "session_id": session.session_id,
            "scenario_title": _extract_scenario_title(scenario),
            "category": sub_cat.sub_title if sub_cat else "Free",
            "created_at": session.created_at,
            "audio_url": session.audio_url,
        })

    return recent_sessions

# 2. [신규] 특정 세션의 상세 스크립트 조회
def get_session_script_detail(db: Session, session_id: int, user_id: int):
    # 1. DB 조회
    result = db.query(ConversationSession, CustomScenario).outerjoin(
        CustomScenario, ConversationSession.scenario_id == CustomScenario.scenario_id
    ).filter(
        ConversationSession.session_id == session_id,
        ConversationSession.user_id == user_id
    ).first()

    # 2. 결과 검증 (None 방어)
    if result is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    session_obj, scenario_obj = result
    
    # 3. JSON 데이터 파싱
    script_data = {}
    if scenario_obj and getattr(scenario_obj, 'generated_script', None):
        script_data = scenario_obj.generated_script
        if isinstance(script_data, str):
            script_data = json.loads(script_data)

    # 4. 데이터 추출
    title = script_data.get("scenario_goal", "실전 회화")
    ai_passage = script_data.get("scenario_goal", "지문 정보 없음")
    full_turns = script_data.get("turns", [])

    # 5. SentenceLog 리스트를 딕셔너리로 확실하게 변환
    logs = db.query(SentenceLog).filter(SentenceLog.session_id == session_id).order_by(SentenceLog.created_at.asc()).all()
    
    scripts_list = [
        {
            "role": log.role,
            "original_text": log.original_text or "",
            "translated_text": log.translated_text,
            "corrected_text": log.corrected_text,
            "feedback_comment": log.feedback_comment,
            "created_at": log.created_at.isoformat() if log.created_at is not None else None
        } for log in logs
    ]

    # 6. 최종 리턴
    return {
        "session_id": session_id,
        "scenario_title": title,
        "ai_passage_en": ai_passage,
        "ai_passage_ko": ai_passage,
        "full_turns": full_turns,
        "scripts": scripts_list
    }
