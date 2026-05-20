from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# ==========================================
# [기본 엔티티 스키마]
# ==========================================
class VocabularyBase(BaseModel):
    target_word: str = Field(..., description="영어 정답 단어")
    cefr_level: str = Field(..., description="국제 표준 영어 레벨 (A1~C2)")
    expression: Optional[str] = Field(None, description="영어 전체 예문")
    meaning: Optional[str] = Field(None, description="한국어 해석")
    focus_point: Optional[str] = Field(None, description="집중 훈련 포인트")

class VocabularyResponse(VocabularyBase):
    vocab_id: int
    is_customized: bool

    class Config:
        from_attributes = True

class VocabularyStudyUpdate(BaseModel):
    vocab_id: int
    is_correct: bool
    user_answer: Optional[str] = None

class VocabDetailResponse(BaseModel):
    learning_id: int
    vocab_id: int
    user_answer: str
    created_at: datetime

    class Config:
        from_attributes = True

# ==========================================
# [화면 연동 스키마] 오리지널 기획서 기준
# ==========================================
class VocabularyDashboardResponse(BaseModel):
    """오늘의 어휘 메인 대문 원형 레이아웃 출력용 카운트 데이터"""
    new_words_count: int = Field(..., description="새로운 단어 수")
    review_words_count: int = Field(..., description="복습할 단어 수")
    retry_words_count: int = Field(..., description="재도전 단어 수")

class VocabularyQuizResponse(BaseModel):
    """실전 퀴즈 풀이 화면용 문제 데이터"""
    sentence_id: int
    masked_sentence: str = Field(..., description="____ 로 마스킹 처리된 영어 문장")
    korean_hint: str = Field(..., description="한국어 번역 해석 힌트")
    word_length: int = Field(..., description="정답 단어 알파벳 글자 수")

class AnswerItem(BaseModel):
    sentence_id: int
    user_answer: str

class QuizSessionSubmitRequest(BaseModel):
    """유저가 문제를 다 풀고 결과 보기를 눌렀을 때의 제출 Body"""
    answers: List[AnswerItem]

class QuizResultDetail(BaseModel):
    sentence_id: int
    original_sentence: str = Field(..., description="마스킹이 복원된 전체 원본 영어 문장")
    target_word: str = Field(..., description="실제 정답 단어")
    user_answer: str = Field(..., description="유저가 제출했던 답변")
    is_correct: bool = Field(..., description="정답 여부 (O/X)")

class QuizSessionResultResponse(BaseModel):
    """결과창 화면용 최종 스코어 보드 데이터"""
    total_count: int = Field(..., description="총 문제 수 (setting_count)")
    correct_count: int = Field(..., description="맞힌 문장 개수")
    results: List[QuizResultDetail] = Field(..., description="결과 상세 리스트")



class QuizAnswerCheckRequest(BaseModel):
    """실전 퀴즈 풀이 중 단일 문항에 대한 즉석 검증 요청 바디"""
    sentence_id: int = Field(..., description="현재 풀고 있는 문장 ID")
    user_answer: str = Field(..., description="유저가 입력창에 타이핑한 답변")
    attempt_count: int = Field(1, description="현재 문항 풀이 시도 횟수 (1=힌트제공, 2이상=오답처리)")

class QuizAnswerCheckResponse(BaseModel):
    """GPT의 뉘앙스 분석 힌트가 포함된 즉석 검증 응답 스펙"""
    is_correct: bool = Field(..., description="동적 정답 여부 (O/X)")
    target_word: str = Field(..., description="실제 정답 단어 (프론트엔드 디버깅 및 대조용)")
    hint_message: Optional[str] = Field(None, description="오답 시 GPT가 실시간으로 생성한 뉘앙스 교정 힌트 텍스트")




# 1. 프론트엔드가 보내줄 토글 스위치 데이터 (True 또는 False)
class BookmarkToggleRequest(BaseModel):
    is_bookmarked: bool

# 2. 리스트에서 보여줄 단어 1개의 상세 정보
class BookmarkedVocabItem(BaseModel):
    vocab_id: int
    target_word: str
    expression: Optional[str]
    meaning: Optional[str]

# 3. 프론트엔드에 응답할 최종 리스트 규격
class BookmarkListResponse(BaseModel):
    total_count: int
    items: List[BookmarkedVocabItem]


# 오늘의 학습 통계 및 오답 단어 리스트 반환용 스키마
class DailyStats(BaseModel):
    total_quizzes_today: int
    correct_quizzes_today: int
    accuracy_rate: float

class WrongVocabItem(BaseModel):
    vocab_id: int
    target_word: str
    expression: Optional[str]
    meaning: Optional[str]
    incorrect_count: int

class DailyStudyResponse(BaseModel):
    daily_stats: DailyStats
    wrong_vocab_list: List[WrongVocabItem]