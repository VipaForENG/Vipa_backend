from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.crud import vocabulary as vocab_crud
from app.crud import level as level_crud  # 🔥 [인증/레벨 통합] 레벨 조회 모듈 임포트
from app.core.security import get_current_user_id  # 🔥 [인증/레벨 통합] 토큰 보초병 임포트
from app.schemas.vocabulary import (
    VocabularyDashboardResponse,
    VocabularyQuizResponse,
    QuizSessionSubmitRequest,
    QuizSessionResultResponse
)

router = APIRouter()


@router.get("/dashboard", response_model=VocabularyDashboardResponse)
async def get_vocabulary_dashboard(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)  # 🔥 [인증 통합]: 토큰에서 진짜 유저 ID 추출
):
    """
    [API] 오늘의 어휘 메인 대문 화면 데이터 조회
    
    - 역할: 로그인한 유저의 진짜 레벨을 조회하여 단어 종류별(새 단어, 복습, 재도전) 카운트를 집계합니다.
    """
    # [Pylance 에러 해결]: 실제 crud/level.py에 정의된 get_user_level 함수를 호출합니다.
    user_level_obj = level_crud.get_user_level(db, user_id=current_user_id)
    
    # [Pylance 에러 해결]: 레벨 테스트를 보지 않았거나(None), 필드가 비어있을 경우 기본값 "A1"로 치환하는 방어 코드(Null-Safe)
    user_current_level = user_level_obj.cefr_level if (user_level_obj and user_level_obj.cefr_level) else "A1"
    
    return await vocab_crud.get_dashboard_data(
        db=db, 
        user_id=current_user_id, 
        cefr_level=user_current_level
    )


@router.get("/quiz", response_model=List[VocabularyQuizResponse])
async def get_personalized_quiz(
    new_count: int = 5,     # 프론트가 안 보내면 기본 5개 설정
    review_count: int = 10, # 기본 10개 설정
    retry_count: int = 10,  # 기본 10개 설정
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)  # 🔥 [인증 통합]: 동적 유저 매핑
):
    """
    [API] 맞춤형 분할 퀴즈 세션 생성
    
    - 역할: 사용자가 직접 지정한 비율 데이터와 실제 CEFR 레벨을 대조하여 맞춤형 퀴즈 패키지를 빌드합니다.
    """
    # [Pylance 에러 해결]: 공용 레벨 추출 아키텍처 적용
    user_level_obj = level_crud.get_user_level(db, user_id=current_user_id)
    user_current_level = user_level_obj.cefr_level if (user_level_obj and user_level_obj.cefr_level) else "A1"
    
    return await vocab_crud.get_personalized_quiz(
        db=db, 
        user_id=current_user_id, 
        cefr_level=user_current_level,
        new_count=new_count,
        review_count=review_count,
        retry_count=retry_count
    )


@router.post("/quiz/session", response_model=QuizSessionResultResponse)
async def submit_quiz_session(
    payload: QuizSessionSubmitRequest, 
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)  # 🔥 [인증 통합]: 동적 유저 매핑
):
    """
    [API] 퀴즈 세션 결과 제출 및 배치 채점
    
    - 역할: 유저가 타이핑한 답안 배열을 검증하고, 오답 이력 로그를 누적 반영합니다.
    """
    return await vocab_crud.process_quiz_session(
        db=db, 
        user_id=current_user_id, 
        answers=payload.answers
    )


from app.schemas.vocabulary import QuizAnswerCheckRequest, QuizAnswerCheckResponse

@router.post("/quiz/check", response_model=QuizAnswerCheckResponse)
async def check_quiz_answer(payload: QuizAnswerCheckRequest, db: Session = Depends(get_db)):
    """
    [API] 퀴즈 풀이 중 단일 문항 실시간 검증 (GPT 즉석 힌트 박스 연동용)
    
    - 역할: 유저가 단어를 적고 확인/다음 버튼을 누를 때 호출되어 실시간 정오답 상태와 맞춤형 가이드라인 힌트를 제공합니다.
    """
    return await vocab_crud.check_single_answer_with_hint(
        db=db,
        sentence_id=payload.sentence_id,
        user_answer=payload.user_answer
    )