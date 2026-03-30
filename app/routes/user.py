from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.crud import user as user_crud

router = APIRouter()

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    회원가입 API: 이메일 중복 확인 후 유저와 로봇 데이터를 생성합니다.
    """
    # 1. 이미 가입된 이메일인지 확인
    db_user = user_crud.get_user_by_email(db, email=user_in.email)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="이미 존재하는 이메일입니다."
        )
    
    # 2. 유저 및 로봇 생성 로직 실행 (CRUD 함수 호출)
    new_user = user_crud.create_user(db=db, user_in=user_in)
    
    return new_user