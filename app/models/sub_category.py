from sqlalchemy import Column, Integer, String, TEXT, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class SubCategory(Base):
    __tablename__ = "sub_category"
    sub_cat_id = Column(Integer, primary_key=True)
    main_cat_id = Column(Integer, ForeignKey("main_category.main_cat_id", ondelete="CASCADE"), nullable=False)
    sub_title = Column(String(100), nullable=False)
    ai_role = Column(TEXT)

    main_category = relationship("MainCategory", back_populates="sub_categories")