from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ScenarioResponse(BaseModel):
    scenario_id: int
    difficulty_level: str
    generated_script: str
    created_at: datetime
    class Config: from_attributes = True

class SessionCreate(BaseModel):
    scenario_id: int

class SessionResponse(BaseModel):
    session_id: int
    user_id: int
    scenario_id: int
    audio_url: Optional[str] = None
    created_at: datetime
    class Config: from_attributes = True