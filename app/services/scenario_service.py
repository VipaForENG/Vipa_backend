# app/services/scenario_service.py
import json
# AsyncSession 대신 Session을 임포트 (타입 힌트용)
from sqlalchemy.orm import Session 
from sqlalchemy import select
from app.models.custom_scenario import CustomScenario
from app.models.level import LevelTestResult, UserLevel
from app.models.category import SubCategory
from app.core.ai_client import client, MODEL_NAME
from fastapi import HTTPException
import json
from app.schemas.scenario import EvaluationRequest, EvaluationResponse, HintRequest, HintResponse, SessionCompleteResponse, SessionCompleteRequest
from app.models.sentence_log import SentenceLog
from app.models.conversation_session import ConversationSession
from app.models.study_log import StudyLog
from app.models.user import User
from sqlalchemy import func
from app.models.conversation_turn import ConversationTurn

# db: AsyncSession -> db: Session 으로 변경
# 실전회화 시나리오 생성 서비스
async def create_custom_scenario(
    db: Session, 
    user_id: int, 
    sub_cat_id: int, 
    test_id: int | None = None
):
    # 1. 사용자의 CEFR 레벨 조회 (L3 해결 포인트: await 제거)
    if test_id is None:
        level_stmt = (
            select(LevelTestResult.test_id, UserLevel.cefr_level)
            .join(UserLevel, UserLevel.user_level_id == LevelTestResult.user_level_id)
            .where(UserLevel.user_id == user_id)
            .order_by(LevelTestResult.created_at.desc())
            .limit(1)
        )
        level_row = db.execute(level_stmt).first()
        test_id = level_row.test_id if level_row else None
        cefr_level = level_row.cefr_level if level_row else "A1"
    else:
        stmt = (
            select(UserLevel.cefr_level)
            .join(LevelTestResult)
            .where(LevelTestResult.test_id == test_id, UserLevel.user_id == user_id)
        )
        result = db.execute(stmt) # <--- 범인 체포 완료 (await 삭제)
        cefr_level = result.scalar()
        if not cefr_level:
            raise ValueError(f"해당 사용자의 레벨 테스트(ID: {test_id})를 찾을 수 없습니다.")

    # 2. 서브 카테고리의 기본 AI 역할 조회 (L3 해결 포인트: await 제거)
    sub_stmt = select(SubCategory).where(SubCategory.sub_cat_id == sub_cat_id)
    sub_result = db.execute(sub_stmt) # <--- 범인 체포 완료 (await 삭제)
    sub_cat = sub_result.scalar()

    if not sub_cat:
        raise ValueError(f"해당 소분류(ID: {sub_cat_id})를 찾을 수 없습니다.")

    # 3. 프롬프트 구성 (동일)
    system_prompt = f"""
    You are an expert AI English Tutor designing a roleplay scenario for a student at the {cefr_level} CEFR level.
    Scenario Context: {sub_cat.sub_title}
    Your Role: {sub_cat.ai_role}
    
    Task:
    Create a highly realistic and extended 17-turn conversation script. 
    The sequence must strictly alternate, starting and ending with the AI. 
    (Sequence: AI -> User -> AI -> User ... Total: exactly 9 AI turns and 8 User turns).
    For the User's turns, provide the 'expected_en' (the ideal correct response) and extract 2-3 essential 'keywords' from that expected response to be used as hints.
    Provide Korean translations ('ko') for all English sentences.
    Adjust all vocabulary and grammar strictly to the {cefr_level} level.
    Ensure the conversation flows naturally step-by-step to achieve the scenario goal.
    
    Format Constraint:
    Return ONLY a valid JSON object with the following exact structure, without any markdown formatting:
    {{
      "scenario_goal": "이 대화의 최종 목표 (한국어로 짧게 작성)",
      "turns": [
        {{ "speaker": "ai", "en": "...", "ko": "..." }},
        {{ "speaker": "user", "expected_en": "...", "ko": "...", "keywords": ["keyword1", "keyword2"] }},
        {{ "speaker": "ai", "en": "...", "ko": "..." }},
        {{ "speaker": "user", "expected_en": "...", "ko": "...", "keywords": ["...", "..."] }},
        ... [Continue strictly alternating until there are 9 'ai' objects and 8 'user' objects] ...
        {{ "speaker": "ai", "en": "...", "ko": "..." }}
      ]
    }}
    """

    # 4. AI 호출 (여기는 AsyncOpenAI 이므로 반드시 await 유지)
    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "system", "content": system_prompt}],
            response_format={ "type": "json_object" },
            stream=False 
        )
        raw_content = response.choices[0].message.content
    except Exception as ai_err:
        raise HTTPException(status_code=500, detail=f"AI 호출 오류: {str(ai_err)}")

    if not raw_content:
        raise HTTPException(status_code=500, detail="AI 응답이 비어있습니다.")

    try:
        script_content = json.loads(raw_content)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail="AI 응답 형식이 올바르지 않습니다.")

    # 5. DB 저장: CustomScenario (대본) 먼저 생성
    new_scenario = CustomScenario(
        user_id=user_id,
        sub_cat_id=sub_cat_id,
        test_id=test_id,
        difficulty_level=cefr_level,
        ai_prompt_used=system_prompt,
        generated_script=script_content
    )
    db.add(new_scenario)
    
    # 🔥 [L5 아키텍처 포인트] flush()의 마법
    db.flush() 

    # 6. DB 저장: 발급받은 scenario_id를 묶어서 ConversationSession (대화방) 생성
    new_session = ConversationSession(
        user_id=user_id,
        scenario_id=new_scenario.scenario_id
    )
    db.add(new_session)
    
    # 두 테이블의 생성 기록을 하나로 묶어서(트랜잭션) 영구 저장
    db.commit() 
    
    db.refresh(new_scenario)
    db.refresh(new_session)

    # 7. 응답 스키마(ScenarioResponse) 규격에 맞게 딕셔너리로 반환
    return {
        "session_id": new_session.session_id,
        "scenario_id": new_scenario.scenario_id,
        "difficulty_level": new_scenario.difficulty_level,
        "generated_script": script_content,
        "created_at": new_scenario.created_at
    }


# 사용자 답변 평가 서비스 (L5 최적화 포인트: GPT-5를 활용한 문맥 기반 생성형 평가)
async def evaluate_user_response(db: Session, req: EvaluationRequest) -> EvaluationResponse:
    # 1. DB에서 저장된 시나리오 불러오기 (동기 처리)
    stmt = select(CustomScenario).where(CustomScenario.scenario_id == req.scenario_id)
    scenario = db.execute(stmt).scalar()
    
    if not scenario:
        raise HTTPException(status_code=404, detail="해당 시나리오를 찾을 수 없습니다.")

    # 2. 이번 턴의 예상 정답(expected_en) 추출
    script_data = scenario.generated_script
    if isinstance(script_data, str):
        script_data = json.loads(script_data)
    turns = script_data.get("turns", [])
    
    # 'user'가 말할 차례인 턴만 골라냅니다.
    user_turns = [t for t in turns if t.get("speaker") == "user"]
    
    if req.turn_index >= len(user_turns):
        raise HTTPException(status_code=400, detail="유효하지 않은 턴 인덱스입니다.")
        
    expected_en = user_turns[req.turn_index].get("expected_en")
    difficulty = scenario.difficulty_level

    # 3. GPT 평가 프롬프트 구성 (가장 중요한 부분)
    system_prompt = f"""
    You are an expert English evaluator.
    The user is an English learner at the {difficulty} CEFR level.
    
    [Context]
    Expected Ideal Answer: "{expected_en}"
    User's Actual Answer: "{req.user_input}"
    
    [Task]
    Evaluate the user's answer.
    1. is_pass: Return 'true' if the user's answer is contextually appropriate and makes sense, EVEN IF it is not exactly the same as the Expected Answer. Return 'false' only if it is completely off-topic or grammatically incomprehensible.
    2. feedback_ko: Explain kindly in Korean what was good, what was wrong, and why it was corrected. If 'is_pass' is false, explain clearly why it was incorrect.
    3. corrected_en: Provide a natural, grammatically correct version of the user's answer, tailored to the {difficulty} level.
    
    [Format Constraint]
    Return ONLY a valid JSON object: {{"is_pass": true/false, "feedback_ko": "string", "corrected_en": "string"}}
    """

    # 4. AI 평가 요청 (비동기 처리)
    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "system", "content": system_prompt}],
            response_format={ "type": "json_object" },
            stream=False 
        )
        raw_content = response.choices[0].message.content
    except Exception as ai_err:
        raise HTTPException(status_code=500, detail=f"평가 엔진 호출 오류: {str(ai_err)}")

    if not raw_content:
        raise HTTPException(status_code=500, detail="AI 응답이 비어있습니다.")
    
    
    # 5. AI 응답 파싱
    try:
        eval_result = json.loads(raw_content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI 응답 형식이 올바르지 않습니다.")
        
    # 🔥 6. [신규 통합] 응답 파싱이 완료된 후, SentenceLog에 기록 남기기
    try:
        # 1. 교정 데이터 기록 (Dashboard용)
        new_turn = ConversationTurn(
            session_id=req.session_id,
            turn_index=req.turn_index,
            user_input=req.user_input,
            is_pass=eval_result.get("is_pass", False),
            feedback_ko=eval_result.get("feedback_ko"),
            corrected_en=eval_result.get("corrected_en")
        )
        db.add(new_turn)

        # 2. 대화 기록 보존 (Transcript용 - 기존 SentenceLog 유지)
        new_log = SentenceLog(
            session_id=req.session_id,
            sub_cat_id=scenario.sub_cat_id,
            role="user",
            original_text=req.user_input,
            corrected_text=eval_result.get("corrected_en"),
            feedback_comment=eval_result.get("feedback_ko")
        )
        db.add(new_log)
        
        db.commit() # 한 번에 커밋
    except Exception as db_err:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"로그 저장 중 오류: {str(db_err)}")

    return EvaluationResponse(**eval_result)
    
    

# 6. 힌트 제공 서비스 (신규 추가)
def get_hint_for_turn(db: Session, req: HintRequest) -> HintResponse:
    # 1. DB에서 시나리오 조회 (동기)
    stmt = select(CustomScenario).where(CustomScenario.scenario_id == req.scenario_id)
    scenario = db.execute(stmt).scalar()
    
    if not scenario:
        raise HTTPException(status_code=404, detail="해당 시나리오를 찾을 수 없습니다.")

    # 2. 이번 턴의 데이터 추출
    script_data = scenario.generated_script
    if isinstance(script_data, str):
        script_data = json.loads(script_data)
        
    # 이제 안전하게 .get()을 사용할 수 있습니다.
    turns = script_data.get("turns", [])
    user_turns = [t for t in turns if t.get("speaker") == "user"]
    
    if req.turn_index >= len(user_turns):
        raise HTTPException(status_code=400, detail="유효하지 않은 턴 인덱스입니다.")
        
    target_turn = user_turns[req.turn_index]
    expected_en = target_turn.get("expected_en", "")
    keywords = target_turn.get("keywords", [])

    # 3. 힌트 레벨에 따른 텍스트 가공 로직
    if req.hint_level == 1:
        # 1단계: 핵심 단어 조합
        hint_text = ", ".join(keywords) if keywords else "핵심 단어 정보가 없습니다."
        is_penalty = False
        
    elif req.hint_level == 2:
        # 2단계: 문장의 시작 부분 (첫 2단어 추출)
        words = expected_en.split()
        if len(words) >= 2:
            hint_text = f"{words[0]} {words[1]} ..."
        else:
            hint_text = f"{expected_en} ..."
        is_penalty = False
        
    elif req.hint_level == 3:
        # 3단계: 최종 정답 및 오답 처리 경고 플래그
        hint_text = expected_en
        is_penalty = True
        
    else:
        raise HTTPException(status_code=400, detail="힌트 레벨은 1, 2, 3 중 하나여야 합니다.")

    return HintResponse(hint_text=hint_text, is_penalty=is_penalty)

# 7. 세션 완료 처리 서비스
def complete_scenario_session(db: Session, session_id: int) -> SessionCompleteResponse:
    # 1. 3개의 테이블을 조인하여 유저 닉네임과 상황(주제) 추출
    stmt = select(
        ConversationSession.user_id,
        User.nickname.label("nickname"),  # 🔥 'name'을 'nickname'으로 수정 완료
        SubCategory.sub_title.label("situation_title")
    ).join(
        User, User.user_id == ConversationSession.user_id
    ).join(
        CustomScenario, CustomScenario.scenario_id == ConversationSession.scenario_id
    ).join(
        SubCategory, SubCategory.sub_cat_id == CustomScenario.sub_cat_id
    ).where(
        ConversationSession.session_id == session_id
    )
    
    row = db.execute(stmt).first()
    if not row:
        raise HTTPException(status_code=404, detail="해당 세션을 찾을 수 없습니다.")

    user_id = row.user_id
    nickname = row.nickname  # 이제 여기서 nickname 값이 담기게 됩니다.
    situation_title = row.situation_title

    # 2. 교정 받은 문장 수 카운트 (SentenceLog 조회)
    count_stmt = select(func.count(SentenceLog.sentencelog_id)).where(
        SentenceLog.session_id == session_id,
        SentenceLog.role == "user" # 사용자가 대답한 턴(Turn)의 개수
    )
    corrected_count = db.execute(count_stmt).scalar() or 0

    # 3. 보상 시스템 연동 (StudyLog에 에너지 +10 적립)
    new_study_log = StudyLog(
        user_id=user_id,
        type="CONVERSATION",
        session_id=session_id,
        earned_energy=10
    )
    db.add(new_study_log)
    db.commit()

    # 4. 프론트엔드 UI 와이어프레임에 딱 맞는 형식으로 반환
    return SessionCompleteResponse(
        nickname=nickname,
        situation_title=situation_title,
        corrected_count=corrected_count,
        message="오늘의 학습을 완료 했습니다!!!"
    )
