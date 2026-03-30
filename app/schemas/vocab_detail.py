from pydantic import BaseModel
from datetime import datetime

class VocabDetailResponse(BaseModel):
    learning_id: int
    vocab_id: int
    user_answer: str
    created_at: datetime
    class Config: from_attributes = True