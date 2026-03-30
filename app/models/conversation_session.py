from sqlalchemy import Column, Integer, TEXT, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from app.core.database import Base

class ConversationSession(Base):
    __tablename__ = "conversation_session"

    session_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    scenario_id = Column(Integer, ForeignKey("custom_scenario.scenario_id", ondelete="CASCADE"), nullable=False)
    
    created_at = Column(TIMESTAMP, server_default=func.now())
    audio_url = Column(TEXT)                         # 발음 다시듣기를 위한 녹음 파일 경로