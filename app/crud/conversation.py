import json

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

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


def get_conversation_history_dashboard(db: Session, user_id: int):
    recent_query = db.query(ConversationSession, CustomScenario, SubCategory).outerjoin(
        CustomScenario, ConversationSession.scenario_id == CustomScenario.scenario_id
    ).outerjoin(
        SubCategory, CustomScenario.sub_cat_id == SubCategory.sub_cat_id
    ).filter(
        ConversationSession.user_id == user_id
    ).order_by(desc(ConversationSession.created_at)).limit(3).all()

    recent_sessions = []
    for session, scenario, sub_cat in recent_query:
        recent_sessions.append({
            "session_id": session.session_id,
            "scenario_title": _extract_scenario_title(scenario),
            "category": sub_cat.sub_title if sub_cat else "Free",
            "created_at": session.created_at,
            "audio_url": session.audio_url,
        })

    raw_corrections = db.query(SentenceLog).join(
        ConversationSession, SentenceLog.session_id == ConversationSession.session_id
    ).filter(
        ConversationSession.user_id == user_id,
        SentenceLog.role == "user",
        SentenceLog.corrected_text.is_not(None),
    ).order_by(desc(SentenceLog.created_at)).all()

    ai_corrections = [
        {
            "turn_id": log.sentencelog_id,
            "session_id": log.session_id,
            "user_input": log.original_text,
            "corrected_en": log.corrected_text,
            "feedback_ko": log.feedback_comment,
            "created_at": log.created_at,
        }
        for log in raw_corrections
    ]

    progress_query = db.query(
        SubCategory.sub_title,
        func.count(StudyLog.session_id).label("completed_count"),
    ).join(
        ConversationSession, StudyLog.session_id == ConversationSession.session_id
    ).join(
        CustomScenario, ConversationSession.scenario_id == CustomScenario.scenario_id
    ).join(
        SubCategory, CustomScenario.sub_cat_id == SubCategory.sub_cat_id
    ).filter(
        StudyLog.user_id == user_id,
        StudyLog.type == "CONVERSATION",
    ).group_by(SubCategory.sub_title).all()

    category_progress = [
        {"category": title, "completed_sessions": count}
        for title, count in progress_query
    ]

    return recent_sessions, ai_corrections, category_progress
