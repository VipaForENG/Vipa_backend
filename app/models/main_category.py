from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base

class MainCategory(Base):
    __tablename__ = "main_category"
    main_cat_id = Column(Integer, primary_key=True)
    title = Column(String(50), nullable=False)

    sub_categories = relationship("SubCategory", back_populates="main_category")