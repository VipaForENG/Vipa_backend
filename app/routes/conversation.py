from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user_id
from app.crud import conversation as conv_crud
from app.schemas.conversation import ConversationDashboardResponse, ConversationScriptResponse

router = APIRouter()

# =========================================================================
# [Phase 6-1] 실전 회화 학습 내역 리스트 조회
# =========================================================================
@router.get("/dashboard/history", response_model=ConversationDashboardResponse, summary="회화 학습 세션 목록")
async def get_conversation_history_list_api(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """불필요한 통계를 제거하고 세션 히스토리 목록만 반환합니다."""
    sessions = conv_crud.get_conversation_history_list(db=db, user_id=current_user_id)
    
    # 🚨 핵심 수정: 스키마(ConversationDashboardResponse)에 정의된 변수명인 
    # 'recent_sessions'로 맞춰서 리턴해야 Pydantic 500 에러가 나지 않습니다.
    return {"recent_sessions": sessions}

# =========================================================================
# [Phase 6-2] 특정 세션 상세 대화 스크립트 조회 (내보내기용 데이터)
# =========================================================================
@router.get("/dashboard/history/{session_id}", response_model=ConversationScriptResponse, summary="상세 대화 스크립트 조회")
async def get_conversation_script_api(
    session_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    특정 세션(session_id)을 클릭했을 때 호출됩니다.
    유저와 AI가 대화한 전체 스크립트를 시간순으로 반환하며, 교정 내역도 함께 포함됩니다.
    프론트엔드(Flutter)는 이 데이터를 받아 화면에 채팅창처럼 그려주고 PNG/PDF 캡처를 수행합니다.
    """
    script_data = conv_crud.get_session_script_detail(
        db=db, session_id=session_id, user_id=current_user_id
    )
    return script_data