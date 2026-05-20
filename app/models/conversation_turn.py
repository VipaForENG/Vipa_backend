# app/models/conversation_turn.py 파일 생성

from sqlalchemy import Column, Integer, TEXT, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from app.core.database import Base

class ConversationTurn(Base):
    """유저가 발화할 때마다 발생한 AI의 교정 및 피드백 로그를 영구 저장하는 모델"""
    __tablename__ = "conversation_turn"

    turn_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("conversation_session.session_id", ondelete="CASCADE"), nullable=False)
    
    turn_index = Column(Integer, nullable=False)  # 몇 번째 대화 스텝인지
    user_input = Column(TEXT, nullable=False)     # 유저가 타이핑/말한 원문
    is_pass = Column(Boolean, nullable=False)     # 정답 처리 여부
    feedback_ko = Column(TEXT, nullable=True)     # AI 뉘앙스/문법 피드백 한글 설명
    corrected_en = Column(TEXT, nullable=True)    # AI 교정 추천 영어 문장
    
    created_at = Column(TIMESTAMP, server_default=func.now())