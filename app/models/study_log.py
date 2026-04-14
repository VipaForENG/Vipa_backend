from sqlalchemy import Column, Index, Integer, String, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from app.core.database import Base

class StudyLog(Base):
    __tablename__ = "study_log"
    studylog_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    type = Column(String(20), nullable=False) # 'CONVERSATION', 'VOCABULARY'
    session_id = Column(Integer, ForeignKey("conversation_session.session_id"), nullable=True)
    study_id = Column(Integer, ForeignKey("vocabulary_study.study_id"), nullable=True)
    earned_energy = Column(Integer, default=10)
    created_at = Column(TIMESTAMP, server_default=func.now())



    __table_args__ = (
        Index('idx_studylog_user_id_created_at', 'user_id', 'created_at'),
    )