# app/api/v1/endpoints/scenarios.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session  # [L3 교정] AsyncSession 대신 Session 사용
from app.core.database import get_db

# Phase 1, Phase 2 스키마 통합 임포트
from app.schemas.scenario import (
    ScenarioCreate, 
    ScenarioResponse, 
    EvaluationRequest, 
    EvaluationResponse,
    HintRequest,
    HintResponse,
    SessionCompleteRequest,
    SessionCompleteResponse
)   
# Phase 1, Phase 2 서비스 통합 임포트
from app.services.scenario_service import (
    create_custom_scenario, 
    evaluate_user_response,
    get_hint_for_turn,
    complete_scenario_session
)
from app.services.audio_service import save_audio_file


router = APIRouter()

# ==========================================
# [Phase 1] 시나리오 생성 엔드포인트
# ==========================================
@router.post("/generate", response_model=ScenarioResponse)
async def generate_scenario(
    req: ScenarioCreate, 
    db: Session = Depends(get_db)  # 수정됨: Session
):
    """
    실시간 AI 시나리오 생성 엔드포인트
    """
    try:
        new_scenario = await create_custom_scenario(
            db=db,
            user_id=req.user_id,
            sub_cat_id=req.sub_cat_id,
            test_id=req.test_id
        )
        return new_scenario
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시나리오 생성 실패: {str(e)}")


# ==========================================
# [Phase 2] 사용자 발화 평가 엔드포인트 (신규)
# ==========================================
@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_scenario_turn(
    req: EvaluationRequest,
    db: Session = Depends(get_db)
):
    """
    문맥 기반 생성형 평가 (Generative Evaluation) 엔진
    1. 사용자의 발화(user_input)와 턴 인덱스 수신
    2. DB에서 해당 턴의 예상 정답(expected_en) 추출
    3. GPT-4o-mini 엔진을 통한 문맥/문법 채점 및 교정
    4. 통과 여부 및 한국어 피드백 반환
    """
    try:
        # 서비스 로직 호출 (비동기로 대기)
        eval_result = await evaluate_user_response(db, req)
        return eval_result
    except HTTPException as e:
        # 서비스 레이어에서 던진 HTTP 예외는 그대로 패스
        raise e
    except Exception as e:
        # 예상치 못한 시스템 에러
        raise HTTPException(status_code=500, detail=f"평가 엔진 구동 실패: {str(e)}")
    

# ==========================================
# [Phase 3] 단계별 힌트 제공 엔드포인트
# ==========================================
@router.post("/hint", response_model=HintResponse)
def get_scenario_hint(
    req: HintRequest,
    db: Session = Depends(get_db)
):
    """
    AI 호출 없는 초고속 힌트 시스템
    - 1단계: 핵심 키워드 제공
    - 2단계: 문장 시작 부분 제공
    - 3단계: 전체 정답 제공 및 오답 플래그(is_penalty) 활성화
    """
    try:
        # 동기 함수이므로 await 없이 바로 호출합니다.
        return get_hint_for_turn(db, req)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"힌트 시스템 오류: {str(e)}")
    

# ==========================================
# [Phase 4] 실전 회화 완료 및 결과 집계 엔드포인트
# ==========================================
@router.post("/complete", response_model=SessionCompleteResponse)
def complete_session(
    req: SessionCompleteRequest,
    db: Session = Depends(get_db)
):
    """
    17턴의 대화 종료 시 호출됩니다.
    - 교정 문장 수 집계, 유저 및 상황 정보 조회
    - StudyLog에 경험치(에너지) 적립
    """
    try:
        return complete_scenario_session(db, req.session_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"세션 종료 처리 중 오류: {str(e)}")
    


# ==========================================
# [Phase 5] 오디오 파일 업로드 엔드포인트
# ==========================================
@router.post("/upload/audio/{session_id}")
async def upload_session_audio(
    session_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    세션 전체 녹음 파일을 업로드하고 DB에 URL을 기록합니다.
    """
    url = await save_audio_file(db, session_id, file)
    return {"audio_url": url, "message": "오디오 업로드 성공"}