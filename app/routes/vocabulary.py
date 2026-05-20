from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.core.database import get_db
from app.crud import vocabulary as vocab_crud
from app.crud import level as level_crud  # 🔥 [인증/레벨 통합] 레벨 조회 모듈 임포트
from app.core.security import get_current_user_id  # 🔥 [인증/레벨 통합] 토큰 보초병 임포트
from app.schemas.vocabulary import (
    VocabularyDashboardResponse,
    VocabularyQuizResponse,
    QuizSessionSubmitRequest,
    QuizSessionResultResponse,
    QuizAnswerCheckRequest,
    QuizAnswerCheckResponse,
    BookmarkToggleRequest,
    BookmarkedVocabItem,
    BookmarkListResponse,
    DailyStudyResponse,
    DailyStats,
    WrongVocabItem,
)

router = APIRouter()

# =========================================================================
# API 1: 오늘의 어휘 대문 화면 데이터 조회 (새 단어, 복습, 재도전 카운트)
# =========================================================================
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


# =========================================================================
# API 4: 퀴즈 풀이 중 단일 문항 실시간 검증 (GPT 힌트 연동용)
# =========================================================================
@router.post("/quiz/check", response_model=QuizAnswerCheckResponse)
async def check_quiz_answer(
    payload: QuizAnswerCheckRequest, 
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)  # 🔥 [인증 통합]: 유저 추적용
):
    """
    [API] 퀴즈 풀이 중 단일 문항 실시간 검증 (GPT 즉석 힌트 박스 연동용)
    
    - 역할: 유저가 단어를 적고 확인을 누를 때마다 호출됩니다.
    - 1차 시도: DB 감점 없이 힌트만 제공
    - 2차 시도: GPT 힌트 제공 및 DB에 오답(WRONG) 기록 반영
    """
    return await vocab_crud.check_single_answer_with_hint(
        db=db,
        user_id=current_user_id,          # 🔥 CRUD에 유저 ID 전달
        sentence_id=payload.sentence_id,
        user_answer=payload.user_answer,
        attempt_count=payload.attempt_count # 🔥 몇 번째 시도인지 전달
    )



# =========================================================================
# API 1: 즐겨찾기 토글 (On/Off) 설정
# =========================================================================
@router.put("/{vocab_id}/bookmark", summary="학습 문장 즐겨찾기 토글")
async def toggle_bookmark(
    vocab_id: int, 
    request: BookmarkToggleRequest, 
    db: Session = Depends(get_db), 
    current_user_id: int = Depends(get_current_user_id)  # � [인증 통합]: 동적 유저 매핑
):
    """
    클라이언트에서 전달받은 즐겨찾기 상태(True/False)를 DB에 반영합니다.
    """
    # CRUD 모듈 호출하여 데이터베이스 처리 위임
    record = vocab_crud.toggle_bookmark(
        db=db, 
        user_id=current_user_id, 
        vocab_id=vocab_id, 
        is_bookmarked=request.is_bookmarked
    )
    
    return {
        "message": "즐겨찾기 상태가 성공적으로 변경되었습니다.", 
        "vocab_id": vocab_id, 
        "is_bookmarked": record.is_bookmarked
    }

# =========================================================================
# API 2: 즐겨찾기한 문장 리스트 조회
# =========================================================================
@router.get("/bookmarks", response_model=BookmarkListResponse, summary="즐겨찾기 문장 리스트 조회")
async def get_bookmarked_list(
    db: Session = Depends(get_db), 
    current_user_id: int = Depends(get_current_user_id)  # � [인증 통합]: 동적 유저 매핑
):
    """
    사용자가 즐겨찾기한 문장과 단어 리스트를 조회하여 스키마 규격에 맞춰 반환합니다.
    """
    # CRUD 모듈에서 조인된 데이터 리스트 가져오기
    results = vocab_crud.get_bookmarked_list(db=db, user_id=current_user_id)

    # 프론트엔드 응답용 스키마 조립 로직
    items = []
    for vocab, study in results:
        items.append(
            BookmarkedVocabItem(
                vocab_id=vocab.vocab_id,
                target_word=vocab.target_word,
                expression=vocab.expression,
                meaning=vocab.meaning
            )
        )

    return BookmarkListResponse(
        total_count=len(items),
        items=items
    )



# app/routes/vocabulary.py 내부에 추가

from app.schemas.vocabulary import DailyStudyResponse, DailyStats, WrongVocabItem

# =========================================================================
# API 3: 오늘의 어휘 학습 내역 (통계 + 누적 오답 리스트)
# =========================================================================
@router.get("/history/today", response_model=DailyStudyResponse, summary="오늘의 어휘 학습 내역 및 오답 노트")
async def get_daily_history(
    db: Session = Depends(get_db), 
    current_user_id: int = Depends(get_current_user_id)
):
    """
    1. 오늘 푼 문제 수와 정답률 통계를 계산합니다.
    2. 유저의 누적 오답 단어(틀린 횟수 포함) 리스트를 함께 반환합니다.
    """
    stats_data, wrong_results = vocab_crud.get_daily_study_history(db=db, user_id=current_user_id)

    # 1. 통계 데이터 조립
    daily_stats = DailyStats(**stats_data)

    # 2. 오답 리스트 조립
    wrong_vocab_list = []
    for vocab, study in wrong_results:
        wrong_vocab_list.append(
            WrongVocabItem(
                vocab_id=vocab.vocab_id,
                target_word=vocab.target_word,
                expression=vocab.expression,
                meaning=vocab.meaning,
                incorrect_count=study.incorrect_count
            )
        )

    return DailyStudyResponse(
        daily_stats=daily_stats,
        wrong_vocab_list=wrong_vocab_list
    )




