from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

class ScenarioCreate(BaseModel):
    """시나리오 생성 요청을 위한 스키마"""
    user_id: int
    sub_cat_id: int
    test_id: int


# 시나리오 생성 API의 응답 스키마
class ScenarioResponse(BaseModel):
    scenario_id: int
    session_id: int
    difficulty_level: str
    generated_script: Dict[str, Any]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# 시나리오 세션 생성 요청 스키마
class SessionCreate(BaseModel):
    scenario_id: int

# 시나리오 세션 생성 응답 스키마
class SessionResponse(BaseModel):
    session_id: int
    user_id: int
    scenario_id: int
    audio_url: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# 시나리오 평가 요청 스키마
class EvaluationRequest(BaseModel):
    session_id: int
    scenario_id: int
    turn_index: int       # 몇 번째 사용자 턴인지 (0, 1, 2...)
    user_input: str       # 사용자가 실제로 발화/입력한 문장

# 시나리오 평가 응답 스키마
class EvaluationResponse(BaseModel):
    is_pass: bool         # 문맥상 통과 여부 (정답 처리)
    feedback_ko: str      # 왜 틀렸는지, 혹은 어떻게 더 좋게 말하는지 한국어 설명
    corrected_en: str     # 사용자의 수준에 맞춘 교정된 영어 문장


# 시나리오 힌트 요청 스키마
class HintRequest(BaseModel):
    scenario_id: int
    turn_index: int       # 몇 번째 사용자 턴인지
    hint_level: int       # 1(키워드), 2(시작 문구), 3(전체 정답)

# 시나리오 힌트 응답 스키마
class HintResponse(BaseModel):
    hint_text: str        # 가공된 힌트 내용
    is_penalty: bool      # 3단계 진입 시 오답(감점) 처리 플래그


# 세션 완료 요청 스키마
class SessionCompleteRequest(BaseModel):
    session_id: int

# 세션 완료 응답 스키마
class SessionCompleteResponse(BaseModel):
    nickname: str          # UI: {user}님이 대화 중
    situation_title: str    # UI: 오늘의 {situation} 학습 정보
    corrected_count: int    # UI: AI 교정 받은 문장 ? 개
    message: str            # UI: 오늘의 학습을 완료 했습니다!!!