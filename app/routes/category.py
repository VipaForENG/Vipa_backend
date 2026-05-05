from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.category import MainCategory, SubCategory

router = APIRouter()



@router.get("/main-categories")
@router.get("/main-categories")
async def get_main_categories(db: Session = Depends(get_db)):
    categories = db.query(MainCategory).all()
    # [L3 디버깅] 서버가 실제로 조회한 데이터 개수 출력
    print(f"🔍 [DEBUG] 조회된 메인 카테고리 개수: {len(categories)}")
    
    # 만약 0개라면, 서버는 데이터가 없는 DB에 연결된 것입니다.
    return categories

@router.get("/sub-categories/{main_cat_id}")
async def get_sub_categories(main_cat_id: int, db: Session = Depends(get_db)):
    # 특정 메인 카테고리에 속한 서브 카테고리 필터링
    return db.query(SubCategory).filter(SubCategory.main_cat_id == main_cat_id).all()