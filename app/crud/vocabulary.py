import re
from typing import List
from sqlalchemy.orm import Session
from datetime import date,datetime
from sqlalchemy import func, desc, Date, cast



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
        new_words_count=min(new_count, 5),  # 18만 개가 남아있어도 화면엔 최대 5로 표시
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

async def check_single_answer_with_hint(
    db: Session, 
    user_id: int,          
    sentence_id: int, 
    user_answer: str,
    attempt_count: int = 1  
) -> QuizAnswerCheckResponse:
    """
    [무한 루프 방지 완료] 2회차 오답 시 재시도를 차단하고 종료 신호를 송신합니다.
    """
    vocab = db.query(Vocabulary).filter(Vocabulary.vocab_id == sentence_id).first()
    
    if not vocab:
        mock_db = {
            1: {"word": "appointment", "expr": "I want to make an appointment with the doctor."},
            2: {"word": "circumstances", "expr": "Despite the challenging circumstances, she managed to pass."},
            3: {"word": "decision", "expr": "Please make your decision now for the final contract."}
        }
        mock_item = mock_db.get(sentence_id, {"word": "unknown", "expr": ""})
        true_word = mock_item["word"]
        orig_expr = mock_item["expr"]
        is_mock_data = True
    else:
        true_word = vocab.target_word
        orig_expr = vocab.expression or ""
        is_mock_data = False

    is_correct = user_answer.strip().lower() == true_word.strip().lower()
    hint_message = None
    can_retry = False  # 기본값은 재시도 불가

    if is_correct:
        # 맞췄으면 당연히 더 풀 필요 없음
        if not is_mock_data:
            update_vocab_study_result(db, user_id, sentence_id, is_correct=True)
        can_retry = False
            
    else:
        # 🌟 틀렸을 때의 분기 처리
        if attempt_count == 1:
            # [1회차 오답] -> 기회를 한 번 더 주고(can_retry=True), GPT 힌트 생성
            can_retry = True
            hint_message = await generate_wrong_answer_hint(
                target_word=true_word,
                user_answer=user_answer,
                context_sentence=orig_expr
            )
        else:
            # [2회차 이상 오답] -> 기회 박탈(can_retry=False), DB에 WRONG 최종 기록
            can_retry = False
            if not is_mock_data:
                update_vocab_study_result(db, user_id, sentence_id, is_correct=False)
            hint_message = "기회를 모두 소진하셨습니다. 정답을 확인하고 다음 문제로 이동하세요!"

    return QuizAnswerCheckResponse(
        is_correct=is_correct,
        target_word=true_word,
        hint_message=hint_message,
        can_retry=can_retry  # 🌟 프론트엔드에게 통제권 이양
    )



def toggle_bookmark(db: Session, user_id: int, vocab_id: int, is_bookmarked: bool) -> VocabularyStudy:
    """
    [로직 흐름]
    1. 유저 ID와 단어 ID로 기존 학습 이력을 조회합니다.
    2. 이력이 없다면 새로 생성하면서 즐겨찾기 상태를 주입합니다.
    3. 이력이 있다면 기존 레코드의 즐겨찾기 상태만 업데이트합니다.
    """
    study_record = db.query(VocabularyStudy).filter(
        VocabularyStudy.user_id == user_id,
        VocabularyStudy.vocab_id == vocab_id
    ).first()

    if not study_record:
        # 단어를 학습하기 전에 즐겨찾기를 먼저 누른 경우 방어 로직
        study_record = VocabularyStudy(
            user_id=user_id,
            vocab_id=vocab_id,
            status="LEARNING",
            incorrect_count=0,
            is_bookmarked=is_bookmarked
        )
        db.add(study_record)
    else:
        # 기존 학습 기록 상태 업데이트
        study_record.is_bookmarked = is_bookmarked

    db.commit()
    db.refresh(study_record) # 커밋 후 최신 상태를 메모리에 반영하여 반환
    
    return study_record

def get_bookmarked_list(db: Session, user_id: int):
    """
    [로직 흐름]
    1. Vocabulary(단어 마스터) 테이블과 VocabularyStudy(학습 이력) 테이블을 조인합니다.
    2. 특정 유저의 이력 중 즐겨찾기가 켜져 있는(True) 데이터만 필터링합니다.
    3. 가장 최근에 업데이트된(즐겨찾기 한) 순서대로 내림차순 정렬하여 반환합니다.
    """
    results = db.query(Vocabulary, VocabularyStudy).join(
        VocabularyStudy, Vocabulary.vocab_id == VocabularyStudy.vocab_id
    ).filter(
        VocabularyStudy.user_id == user_id,
        VocabularyStudy.is_bookmarked == True
    ).all()
    
    return results



def get_daily_study_history(db: Session, user_id: int):
    today = date.today()

    # ---------------------------------------------------------
    # 1. [오늘의 통계]: 오늘 업데이트(학습)된 단어들의 수량 파악
    # ---------------------------------------------------------
    # (💡 updated_at 컬럼을 Date 타입으로 캐스팅하여 오늘 날짜와 비교)
    today_records = db.query(VocabularyStudy).filter(
    VocabularyStudy.user_id == user_id,
    cast(VocabularyStudy.last_reviewed, Date) == today
    ).all()

    total_today = len(today_records)
    
    # 맞춘 문제 = (전체 푼 문제) - (오늘 상태가 WRONG이 되거나 오답이 증가한 문제)
    # ※ 이 부분은 현재 프로젝트의 '정답/오답' 판별 로직(status 값)에 따라 수정이 필요할 수 있습니다.
    correct_today = sum(1 for r in today_records if r.status == "MEMORIZED" or r.status == "LEARNING")
    
    accuracy = 0.0
    if total_today > 0:
        accuracy = round((correct_today / total_today) * 100, 1)

    daily_stats = {
        "total_quizzes_today": total_today,
        "correct_quizzes_today": correct_today,
        "accuracy_rate": accuracy
    }

    # ---------------------------------------------------------
    # 2. [누적 오답 리스트]: 언제 틀렸든 현재 상태가 WRONG이거나 오답 카운트가 있는 단어들
    # ---------------------------------------------------------
    wrong_results = db.query(Vocabulary, VocabularyStudy).join(
        VocabularyStudy, Vocabulary.vocab_id == VocabularyStudy.vocab_id
    ).filter(
        VocabularyStudy.user_id == user_id,
        # 💡 오답 기준: status가 'WRONG' 이거나 (or) 오답 횟수가 1 이상인 경우
        (VocabularyStudy.status == "WRONG") | (VocabularyStudy.incorrect_count > 0)
    ).all()

    return daily_stats, wrong_results




def update_vocab_study_result(db: Session, user_id: int, vocab_id: int, is_correct: bool) -> VocabularyStudy:
    """단일 문항에 대한 정답/오답 DB 기록 (Upsert)"""
    study_record = db.query(VocabularyStudy).filter(
        VocabularyStudy.user_id == user_id,
        VocabularyStudy.vocab_id == vocab_id
    ).first()

    if not study_record:
        study_record = VocabularyStudy(
            user_id=user_id,
            vocab_id=vocab_id,
            status="MASTERED" if is_correct else "WRONG",
            incorrect_count=0 if is_correct else 1,
            is_bookmarked=False
        )
        db.add(study_record)
    else:
        if is_correct:
            study_record.status = "MASTERED"
        else:
            study_record.status = "WRONG"
            study_record.incorrect_count += 1
            
    # 오늘의 학습 내역 통계에 잡히도록 시간 갱신
    study_record.last_reviewed = datetime.utcnow()
    
    db.commit()
    db.refresh(study_record)
    return study_record