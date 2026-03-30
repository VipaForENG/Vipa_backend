from sqlalchemy import Column, Integer, TEXT, ForeignKey
from app.core.database import Base

class SentenceLog(Base):
    __tablename__ = "sentence_log"
    sentencelog_id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("conversation_session.session_id", ondelete="CASCADE"), nullable=False)
    sub_cat_id = Column(Integer, ForeignKey("sub_category.sub_cat_id"), nullable=False)
    original_text = Column(TEXT)
    corrected_text = Column(TEXT)
    feedback_comment = Column(TEXT)