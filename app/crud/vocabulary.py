import re
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.vocabulary import Vocabulary
from app.models.vocabulary_study import VocabularyStudy
from app.models.vocab_learning_detail import VocabLearningDetail
from app.schemas.vocabulary import (
    VocabularyDashboardResponse,
    VocabularyQuizResponse,
    AnswerItem,
    QuizSessionResultResponse,
    QuizResultDetail
)
from app.utils.gpt5 import generate_wrong_answer_hint
from app.schemas.vocabulary import QuizAnswerCheckResponse


async def get_dashboard_data(db: Session, user_id: int, cefr_level: str) -> VocabularyDashboardResponse:
    """오리지널 기획서 원형 레이아웃 텍스트 카운트 매핑 데이터 계산"""
    # 1. 재도전 단어 카운트 (상태가 WRONG인 단어)
    retry_count = db.query(VocabularyStudy).filter(
        VocabularyStudy.user_id == user_id,
        VocabularyStudy.status == 'WRONG'
    ).count()

    # 2. 복습할 단어 카운트 (기존에 풀이 이력이 있는 MASTERED, LEARNING 단어)
    review_count = db.query(VocabularyStudy).filter(
        VocabularyStudy.user_id == user_id,
        VocabularyStudy.status.in_(['MASTERED', 'LEARNING'])
    ).count()

    # 3. 새로운 단어 카운트 (유저가 한 번도 건드리지 않은 해당 레벨의 단어)
    # [Pylance 에러 해결]: .subquery()는 테이블 객체를 반환하므로 .in_()과 호환되지 않아 타입 에러가 발생합니다.
    # 단일 필드 서브쿼리 역할을 수행하도록 명시하는 .scalar_subquery()를 사용해야 정적 타입 체커를 무결성으로 통과합니다.
    studied_vocab_ids = db.query(VocabularyStudy.vocab_id).filter(
        VocabularyStudy.user_id == user_id
    ).scalar_subquery()
    
    new_count = db.query(Vocabulary).filter(
        Vocabulary.cefr_level == cefr_level,
        ~Vocabulary.vocab_id.in_(studied_vocab_ids)
    ).count()

    # [방어 코드] DB 데이터 적재 전 임시 목업 수치 반환 (UI 확인용)
    if new_count == 0 and review_count == 0 and retry_count == 0:
        return VocabularyDashboardResponse(
            new_words_count=5,
            review_words_count=10,
            retry_words_count=10
        )

    return VocabularyDashboardResponse(
        new_words_count=new_count,
        review_words_count=review_count,
        retry_words_count=retry_count
    )


async def get_personalized_quiz(
    db: Session, 
    user_id: int, 
    cefr_level: str, 
    new_count: int, 
    review_count: int, 
    retry_count: int
) -> List[VocabularyQuizResponse]:
    """
    [기획 반영: 사용자 수량 지정형 퀴즈 빌더]
    유저가 홈 화면에서 직접 조절한 새로운 단어(new_count), 복습(review_count), 재도전(retry_count) 수량에 맞춰
    데이터베이스에서 각각 독립적으로 랜덤 추출한 뒤 하나의 퀴즈 세트로 조립합니다.
    """
    
    # 1. 사용자가 이미 학습한 단어 ID 서브쿼리 (새로운 단어 판별용)
    studied_vocab_ids = db.query(VocabularyStudy.vocab_id).filter(
        VocabularyStudy.user_id == user_id
    ).scalar_subquery()

    # A. 새로운 단어 추출 (지정된 레벨이면서 한 번도 안 푼 단어)
    new_sentences = []
    if new_count > 0:
        new_sentences = db.query(Vocabulary).filter(
            Vocabulary.cefr_level == cefr_level,
            ~Vocabulary.vocab_id.in_(studied_vocab_ids)
        ).order_by(func.random()).limit(new_count).all()

    # B. 복습할 단어 추출 (MASTERED 또는 LEARNING 상태인 단어)
    review_sentences = []
    if review_count > 0:
        review_vocab_ids = db.query(VocabularyStudy.vocab_id).filter(
            VocabularyStudy.user_id == user_id,
            VocabularyStudy.status.in_(['MASTERED', 'LEARNING'])
        ).scalar_subquery()
        
        review_sentences = db.query(Vocabulary).filter(
            Vocabulary.vocab_id.in_(review_vocab_ids)
        ).order_by(func.random()).limit(review_count).all()

    # C. 재도전 단어 추출 (WRONG 상태인 단어)
    retry_sentences = []
    if retry_count > 0:
        retry_vocab_ids = db.query(VocabularyStudy.vocab_id).filter(
            VocabularyStudy.user_id == user_id,
            VocabularyStudy.status == 'WRONG'
        ).scalar_subquery()
        
        retry_sentences = db.query(Vocabulary).filter(
            Vocabulary.vocab_id.in_(retry_vocab_ids)
        ).order_by(func.random()).limit(retry_count).all()

    # 2. 추출된 세 보관함의 리스트를 하나로 결합
    raw_sentences = new_sentences + review_sentences + retry_sentences

    # [방어 코드] 내일 전처리 데이터를 넣기 전, DB가 완전히 비어있을 때의 목업 Fallback
    if not raw_sentences:
        mock_data = [
            {"id": 1, "word": "appointment", "expr": "I want to make an appointment with the doctor.", "mean": "나는 의사와의 예약 조율을 원한다."},
            {"id": 2, "word": "circumstances", "expr": "Despite the challenging circumstances, she managed to pass.", "mean": "도전적인 상황에도 불구하고, 그녀는 합격해냈다."},
            {"id": 3, "word": "decision", "expr": "Please make your decision now for the final contract.", "mean": "최종 계약을 위한 당신의 결정을 지금 내려주세요."}
        ]
        response_mock = []
        for mock in mock_data:
            pattern = re.compile(rf"\b{re.escape(mock['word'])}\b", re.IGNORECASE)
            masked = pattern.sub("____", mock["expr"])
            response_mock.append(VocabularyQuizResponse(
                sentence_id=mock["id"],
                masked_sentence=masked,
                korean_hint=mock["mean"],
                word_length=len(mock["word"])
            ))
        return response_mock

    # 3. 결합된 맞춤형 문제 풀에 대한 동적 마스킹 파이프라인 가동
    quiz_list = []
    for vocab in raw_sentences:
        pattern = re.compile(rf"\b{re.escape(vocab.target_word)}\b", re.IGNORECASE)
        expr_str = vocab.expression or ""
        masked_text = pattern.sub("____", expr_str)
        
        quiz_list.append(VocabularyQuizResponse(
            sentence_id=vocab.vocab_id,
            masked_sentence=masked_text,
            korean_hint=vocab.meaning or "",
            word_length=len(vocab.target_word)
        ))
        
    return quiz_list


async def process_quiz_session(db: Session, user_id: int, answers: List[AnswerItem]) -> QuizSessionResultResponse:
    """
    [오리지널 기획서 규격 기반 배치 채점 엔진]
    - DB에 진짜 단어가 존재할 때만 이력 로그(외래키)를 안전하게 적재합니다.
    - 아직 CSV 전처리 전이라 단어가 없을 경우, DB 저장을 생략(Skip)하고 채점 결과지만 완벽하게 조립하여 반환합니다.
    """
    correct_count = 0
    detailed_results = []
    
    submitted_ids = [item.sentence_id for item in answers]
    vocab_maps = {v.vocab_id: v for v in db.query(Vocabulary).filter(Vocabulary.vocab_id.in_(submitted_ids)).all()}

    for item in answers:
        vocab = vocab_maps.get(item.sentence_id)
        
        # 1. DB에 단어가 없는 목업 모드인지 확인하는 플래그 도입
        if not vocab:
            true_word = "appointment" if item.sentence_id == 1 else ("circumstances" if item.sentence_id == 2 else "decision" if item.sentence_id == 3 else "decision")
            orig_expr = "I want to make an appointment with the doctor." if item.sentence_id == 1 else ("Despite the challenging circumstances, she managed to pass." if item.sentence_id == 2 else "Please make your decision now for the final contract.")
            is_mock_data = True  # 목업 신호 켬
        else:
            true_word = vocab.target_word
            orig_expr = vocab.expression or ""
            is_mock_data = False # 진짜 DB 데이터임
            
        is_correct = item.user_answer.strip().lower() == true_word.strip().lower()
        if is_correct:
            correct_count += 1
            
        # 2. 🔥 [ForeignKey 에러 해결]: 진짜 데이터베이스에 존재하는 단어일 때만 로그 테이블에 Insert 수행
        if not is_mock_data:
            # A. 세션 로그 기록 생성
            learning_detail = VocabLearningDetail(
                user_id=user_id,
                vocab_id=item.sentence_id,
                is_correct=is_correct,
                user_answer=item.user_answer
            )
            db.add(learning_detail)
            
            # B. 단어별 스냅샷 마스터 상태 업데이트
            study_status = db.query(VocabularyStudy).filter(
                VocabularyStudy.user_id == user_id,
                VocabularyStudy.vocab_id == item.sentence_id
            ).first()
            
            if not study_status:
                study_status = VocabularyStudy(
                    user_id=user_id,
                    vocab_id=item.sentence_id,
                    status="MASTERED" if is_correct else "WRONG",
                    incorrect_count=0 if is_correct else 1
                )
                db.add(study_status)
            else:
                if is_correct:
                    study_status.status = "MASTERED"
                else:
                    study_status.status = "WRONG"
                    study_status.incorrect_count += 1
                    
        # 3. 결과창 리포트용 배열은 목업/실전 상관없이 무조건 채워줌 (프론트 렌더링용)
        detailed_results.append(QuizResultDetail(
            sentence_id=item.sentence_id,
            original_sentence=orig_expr,
            target_word=true_word,
            user_answer=item.user_answer,
            is_correct=is_correct
        ))

    # 4. 메모리에 올라온 변경사항 중 진짜 DB 데이터가 섞여있을 때만 최종 커밋 실행 (가짜 데이터로 인한 튕김 방지)
    if any(v is not None for v in vocab_maps.values()):
        db.commit()
    
    return QuizSessionResultResponse(
        total_count=len(answers),
        correct_count=correct_count,
        results=detailed_results
    )

async def check_single_answer_with_hint(db: Session, sentence_id: int, user_answer: str) -> QuizAnswerCheckResponse:
    """
    [실시간 단일 문항 채점 및 GPT 뉘앙스 힌트 파이프라인]
    - 유저가 입력한 텍스트를 즉석 채점합니다.
    - 틀렸을 경우, GPT-5를 가동하여 정답 단어와 유저 오답 간의 차이점을 분석한 힌트를 동적 생성합니다.
    """
    # 1. 대상 단어 레코드 쿼리
    vocab = db.query(Vocabulary).filter(Vocabulary.vocab_id == sentence_id).first()
    
    # [방어 코드] CSV 전처리 전이라 DB가 비어있을 때의 목업 스위칭 (출제용 데이터와 동기화)
    if not vocab:
        mock_db = {
            1: {"word": "appointment", "expr": "I want to make an appointment with the doctor."},
            2: {"word": "circumstances", "expr": "Despite the challenging circumstances, she managed to pass."},
            3: {"word": "decision", "expr": "Please make your decision now for the final contract."}
        }
        
        # sentence_id로 목업 데이터를 찾고, 없으면 fallback 빈값 처리
        mock_item = mock_db.get(sentence_id, {"word": "unknown", "expr": ""})
        true_word = mock_item["word"]
        orig_expr = mock_item["expr"]
    else:
        true_word = vocab.target_word
        orig_expr = vocab.expression or ""

    # 2. 대소문자 및 공백 제거 후 동등 비교 채점
    is_correct = user_answer.strip().lower() == true_word.strip().lower()
    
    # 3. 오답인 경우에만 GPT 가동하여 정밀 오답 힌트 박스 텍스트 빌드
    hint_message = None
    if not is_correct:
        hint_message = await generate_wrong_answer_hint(
            target_word=true_word,
            user_answer=user_answer,
            context_sentence=orig_expr
        )
        
    return QuizAnswerCheckResponse(
        is_correct=is_correct,
        target_word=true_word,
        hint_message=hint_message
    )