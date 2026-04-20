from sqlalchemy import Column, Integer, TEXT, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from app.core.database import Base

class ConversationSession(Base):
    __tablename__ = "conversation_session"

    session_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    
    # 프리토킹(자유대화)일 경우 scenario_id가 없을 수 있으므로 nullable=True로 변경 권장
    scenario_id = Column(Integer, ForeignKey("custom_scenario.scenario_id", ondelete="CASCADE"), nullable=True) 
    
    created_at = Column(TIMESTAMP, server_default=func.now())
    audio_url = Column(TEXT)