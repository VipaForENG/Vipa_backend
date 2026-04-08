from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import cast # Pylance 타입 에러(Column[int] -> int) 방지용

from app.core.database import get_db
# 🔥 EvaluateRequest가 임포트되어 있어야 JSON Body를 정상적으로 파싱합니다.
from app.schemas.level import LevelTestResponse, LevelTestDetail, EvaluateRequest
from app.crud import level as level_crud

# GPT 연동 유틸리티 (실제 AI 호출 담당)
from app.utils.gpt5 import generate_test_questions, analyze_user_answers 

# 🔥 [추가됨] 보안 모듈에서 유저 ID 추출 보초병을 가져옵니다.
from app.core.security import get_current_user_id

router = APIRouter()

# ==========================================
# [1단계: 테스트 시작] - 문장 20개 출제 API
# ==========================================
@router.get("/questions")
async def get_test_questions():
    """
    [API] 프론트엔드에서 '레벨 테스트 시작' 화면에 진입할 때 호출됩니다.
    
    - 역할: GPT-5.4-mini를 호출하여 CEFR A1~C2 난이도가 섞인 20문항을 생성합니다.
    - 반환: JSON 배열 형태의 문제 리스트
    """
    # AI에게 문제 생성을 지시하고 결과를 기다립니다.
    questions = await generate_test_questions()
    
    # 생성된 문제를 프론트엔드로 전달합니다.
    return {"questions": questions}


# ==========================================
# [2단계: 결과 제출 및 분석] - 정밀 채점 API
# ==========================================
@router.post("/evaluate", response_model=LevelTestDetail)
async def evaluate_test(
    request: EvaluateRequest, # 개별 파라미터 대신 Pydantic 모델 하나로 묶어서 JSON Body로 받습니다.
    db: Session = Depends(get_db),
    # 🔥 [추가됨] 프론트엔드가 헤더에 보낸 토큰을 검사해 유저 ID를 뽑아냅니다.
    current_user_id: int = Depends(get_current_user_id) 
):
    """
    [API] 사용자가 20문제를 모두 풀고 '제출' 버튼을 눌렀을 때 호출됩니다.
    
    - 역할: 제출된 20개의 답변을 AI가 분석하고, 성적을 DB에 저장한 뒤 최종 성적표를 반환합니다.
    - 반환: 최종 레벨, 점수, 취약점 태그, 상세 JSON 프로필 (LevelTestDetail 스키마 규격)
    """
    
    # --- Logic 1: AI 정밀 분석 ---
    # 프론트엔드에서 넘겨준 20개의 답변 리스트(request.user_answers)를 GPT에게 보냅니다.
    analysis_result = await analyze_user_answers(request.user_answers)
    
    
    # --- Logic 2: 유저 메인 레벨 갱신 (DB Upsert) ---
    # 🔥 안전하게 추출된 current_user_id를 사용하여 DB를 업데이트합니다!
    user_level = level_crud.create_or_update_user_level(
        db, 
        user_id=current_user_id,
        cefr_level=analysis_result["cefr_level"],
        overall_score=analysis_result["overall_score"]
    )
    
    
    # --- Logic 3: 상세 분석 기록 저장 (History) ---
    # 나중에 실전 회화 모듈에서 꺼내 쓸 수 있도록, 이번 테스트의 상세 분석 JSON과 태그를 기록으로 남깁니다.
    test_record = level_crud.create_test_result(
        db,
        # DB flush로 생성된 ID를 꺼내옵니다. (cast를 써서 Pylance 경고를 막습니다)
        user_level_id=cast(int, user_level.user_level_id), 
        raw_analysis=analysis_result["raw_analysis_json"],
        tags=analysis_result["weakness_tags"]
    )
    
    
    # --- Logic 4: 최종 성적표 조립 및 반환 ---
    # 프론트엔드가 요구하는 `LevelTestDetail` 스키마(응답 모델)에 맞춰서 반환합니다.
    return {
        "cefr_level": user_level.cefr_level,
        "overall_score": user_level.overall_score,
        "raw_analysis_json": test_record.raw_analysis_json,
        "weakness_tags": test_record.weakness_tags,
        "created_at": test_record.created_at
    }