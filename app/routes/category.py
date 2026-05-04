from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.category import MainCategory, SubCategory

router = APIRouter()



@router.get("/main-categories")
async def get_main_categories(db: Session = Depends(get_db)):
    # 모든 메인 카테고리를 가져옴
    return db.query(MainCategory).all()

@router.get("/sub-categories/{main_cat_id}")
async def get_sub_categories(main_cat_id: int, db: Session = Depends(get_db)):
    # 특정 메인 카테고리에 속한 서브 카테고리 필터링
    return db.query(SubCategory).filter(SubCategory.main_cat_id == main_cat_id).all()