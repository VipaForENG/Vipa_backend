from pydantic import BaseModel
from typing import Optional, List, Dict, Any  # 꼭 필요한 것만 남기거나 사용처 확인
from datetime import datetime

# 1. 레벨 테스트 결과 요약 (기본)
class LevelTestResponse(BaseModel):
    cefr_level: str
    overall_score: float
    weakness_tags: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# 2. GPT-5 분석 상세 데이터 
class LevelTestDetail(LevelTestResponse):
    raw_analysis_json: Dict[str, Any] 

# 3. 여러 테스트 기록을 리스트로 보낼 때 (List 활용 예시)
class LevelTestList(BaseModel):
    total_count: int
    results: List[LevelTestResponse]