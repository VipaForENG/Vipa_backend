from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any

from app.core.database import get_db
from app.api import deps  # JWT 유저 인증 의존성
from app.schemas.home import HomeSummaryResponse
from app.crud import log as log_crud
from app.models.user import User

router = APIRouter()

# 홈 화면 요약 정보 API
@router.get("/summary", response_model=HomeSummaryResponse)
async def read_home_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    홈 화면에 필요한 모든 정보를 한 번에 반환합니다.
    - 내 랭킹 및 상위 % (study_count 기준)
    - 최근 7일간의 일별 학습 횟수 (막대 그래프용)
    - 이번 주 출석 요일 리스트 (월-일)
    - 현재 학습 성취도
    """
    try:
        summary = log_crud.get_home_summary(db, user_id=current_user.user_id)
        return summary
    except Exception as e:
        # 로그 요약 실패 시 에러 처리
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"홈 화면 데이터를 불러오는 중 오류가 발생했습니다: {str(e)}"
        )