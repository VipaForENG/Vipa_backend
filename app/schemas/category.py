from pydantic import BaseModel
from typing import List, Optional

class SubCategoryResponse(BaseModel):
    sub_cat_id: int
    sub_title: str
    ai_role: Optional[str] = None
    class Config: from_attributes = True

class MainCategoryResponse(BaseModel):
    main_cat_id: int
    title: str
    sub_categories: List[SubCategoryResponse] = []
    class Config: from_attributes = True