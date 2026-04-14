from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api import deps
from app.models.user import User
from app.utils import gpt5
from app.crud import summary as summary_crud  # 1. 집계 CRUD 임포트 추가
from app.models.level import UserLevel
from app.models.study_log import StudyLog
from pydantic import BaseModel
from typing import List

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    history: List[dict] = []

@router.post("/talk")
async def talking_api(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    # 1. user_levels 테이블에서 해당 유저의 레벨 정보 조회
    # 가장 최근에 테스트한 결과를 가져온다고 가정합니다.
    user_level_record = db.query(UserLevel)\
        .filter(UserLevel.user_id == current_user.user_id)\
        .first()

    # 만약 레벨 테스트 기록이 없다면 기본값인 'A1'으로 설정
    current_cefr: str = "A1"
    if user_level_record and user_level_record.cefr_level:
        current_cefr = str(user_level_record.cefr_level) 

    # 이제 Pylance가 안심하고 넘어갑니다.
    ai_data = await gpt5.get_chat_response(
        user_message=request.message,
        history=request.history,
        cefr_level=current_cefr
    )

    # 3. 학습 로그 및 집계 업데이트 (기존과 동일)
    new_log = StudyLog(
        user_id=current_user.user_id,
        type="CONVERSATION",
        earned_energy=15
    )
    db.add(new_log)
    
    summary_crud.update_daily_summary(
        db, 
        user_id=current_user.user_id, 
        study_type="CONVERSATION", 
        energy=15
    )

    current_user.study_count += 1 
    db.commit()

    # AI 답변에 이번에 획득한 에너지를 합쳐서 보내주면 
    # 앱에서 "+15 Energy" 같은 애니메이션을 띄우기 좋습니다.
    return {
        **ai_data,
        "earned_energy": 15
    }