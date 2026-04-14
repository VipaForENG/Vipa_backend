from pydantic import BaseModel
from typing import List, Dict
class WeeklyEnergyData(BaseModel):
    date: str
    conv_energy: int   # 회화로 얻은 에너지
    vocab_energy: int  # 어휘로 얻은 에너지
    total_energy: int  # 합계 (막대 전체 높이)

    
class HomeSummaryResponse(BaseModel):
    nickname: str
    tier: str # 'BRONZE', 'SILVER' 등 로직에 따른 티어
    top_percent: float # 상위 %
    weekly_data: List[WeeklyEnergyData] # [{'date': '2024-03-20', 'count': 5}, ...]
    attendance: List[str] # ["월", "화", "금"] 등 로그가 존재하는 요일
    study_achievement_rate: int # 목표 대비 달성률 (예: 90)