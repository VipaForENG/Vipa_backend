from sqlalchemy import Column, Integer, String, TEXT, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class MainCategory(Base):
    __tablename__ = "main_category"
    main_cat_id = Column(Integer, primary_key=True)
    title = Column(String(50), nullable=False)

    sub_categories = relationship("SubCategory", back_populates="main_category")
    
class SubCategory(Base):
    __tablename__ = "sub_category"
    sub_cat_id = Column(Integer, primary_key=True, index=True) 
    # ondelete="CASCADE" 추가를 권장합니다.
    main_cat_id = Column(Integer, ForeignKey("main_category.main_cat_id", ondelete="CASCADE"), nullable=False)
    sub_title = Column(String(100), nullable=False)
    ai_role = Column(TEXT, nullable=False)

    main_category = relationship("MainCategory", back_populates="sub_categories")