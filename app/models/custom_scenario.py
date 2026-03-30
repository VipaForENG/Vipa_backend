from sqlalchemy import Column, Integer, String, TEXT, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from app.core.database import Base

class CustomScenario(Base):
    __tablename__ = "custom_scenario"

    scenario_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    sub_cat_id = Column(Integer, ForeignKey("sub_category.sub_cat_id"), nullable=False)
    test_id = Column(Integer, ForeignKey("level_test_results.test_id"), nullable=True)
    
    difficulty_level = Column(String(50))            # 생성 시 적용된 난이도
    ai_prompt_used = Column(TEXT)                    # 사용된 프롬프트 전문
    generated_script = Column(TEXT)                  # AI가 생성한 실제 지문
    created_at = Column(TIMESTAMP, server_default=func.now())