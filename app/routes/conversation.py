from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user_id
from app.crud import conversation as conv_crud
from app.schemas.conversation import ConversationDashboardResponse

router = APIRouter()


# app/routes/scenario.py 맨 하단에 붙여넣기

# 필요한 스키마를 상단 임포트 구역에 명시하거나 즉석 활용하세요.
from app.schemas.conversation import ConversationDashboardResponse  # 해당 스키마 파일 생성 필수
from app.core.security import get_current_user_id

# =========================================================================
# [Phase 6] 마이페이지 실전 회화 통합 대시보드 리스트 조회
# =========================================================================
@router.get("/dashboard/history", response_model=ConversationDashboardResponse, summary="실전 회화 학습 내역 대시보드")
async def get_conversation_history_dashboard_api(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)  # [인증 통합]: 안전한 토큰 보안 가동
):
    """
    유저가 마이페이지나 학습 대시보드에 진입할 때 호출되는 API입니다.
    - 최근 대화 세션 내역 (최대 3개)
    - AI 영어 문장 교정 노트 (최대 5개)
    - 카테고리별 완료 진도 통계
    """
    # 💡 임포트한 crud 경로명에 맞춰 적절히 수정해 주세요 (예: vocab_crud 또는 conv_crud)
    recent_sessions, ai_corrections, category_progress = conv_crud.get_conversation_history_dashboard(
        db=db, user_id=current_user_id
    )

    return {
        "recent_sessions": recent_sessions,
        "ai_corrections": ai_corrections,
        "category_progress": category_progress
    }