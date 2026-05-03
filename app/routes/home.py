from fastapi import APIRouter, Depends, HTTPException, status

# 비동기 세션을 처리하기 위해 AsyncSession 임포트
from sqlalchemy.ext.asyncio import AsyncSession 
from typing import Any

from app.core.database import get_async_db
from app.api import deps  # JWT 유저 인증 의존성
from app.schemas.home import HomeSummaryResponse

from app.crud.daily_summary import daily_summary_crud as summary_crud
from app.models.user import User

router = APIRouter()

# 홈 화면 요약 정보 API
@router.get("/summary", response_model=HomeSummaryResponse)
async def read_home_summary(
    # 🚨 [수정 3] Session -> AsyncSession으로 타입 변경
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    홈 화면에 필요한 모든 정보를 한 번에 반환합니다.
    """
    try:
        # 이제 Pylance가 summary_crud(인스턴스) 내부의 get_home_summary를 정상 인식합니다.
        summary = await summary_crud.get_home_summary(db, user_id=current_user.user_id)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"홈 화면 데이터를 불러오는 중 오류가 발생했습니다: {str(e)}"
        )