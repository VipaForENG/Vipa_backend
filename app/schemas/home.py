from typing import List
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class WeeklyEnergyData(BaseModel):
    date: str
    conv_energy: int
    vocab_energy: int
    total_energy: int

class HomeSummaryResponse(BaseModel):
    nickname: str
    tier: str
    top_percent: float
    total_learning_energy: int       
    today_vocabulary_energy: int     
    today_conversation_energy: int   
    weekly_data: List[WeeklyEnergyData]
    attendance: List[str]
    attendance_dates: List[str]
    continuous_attendance_count: int
    study_achievement_rate: int

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )