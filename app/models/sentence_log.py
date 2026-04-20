from sqlalchemy import Column, Integer, String, TEXT, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from app.core.database import Base

class SentenceLog(Base):
    __tablename__ = "sentence_log"
    sentencelog_id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("conversation_session.session_id", ondelete="CASCADE"), nullable=False)
    
    # 자유대화면 카테고리가 없을 수 있으므로 nullable=True
    sub_cat_id = Column(Integer, ForeignKey("sub_category.sub_cat_id"), nullable=True) 
    
    # 🔥 [추가 필수] 발화자 구분 ('user' 또는 'assistant')
    role = Column(String(20), nullable=False, default="user") 
    
    # 유저의 원래 말 OR AI의 대답 (둘 다 여기에 저장)
    original_text = Column(TEXT) 
    
    # 아래는 부가 정보들
    corrected_text = Column(TEXT) # 문법 교정된 문장 (유저 발화일 때만 사용)
    translated_text = Column(TEXT) # 한국어 번역 (AI 발화일 때만 사용)
    feedback_comment = Column(TEXT) # 피드백 내용
    
    # 🔥 [추가 권장] 대화 순서 보장을 위한 시간
    created_at = Column(TIMESTAMP, server_default=func.now())