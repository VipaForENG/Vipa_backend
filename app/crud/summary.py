# app/crud/summary.py (새로 생성하거나 chat.py에 포함)
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from app.models.summary import DailyStudySummary
from datetime import datetime

def update_daily_summary(db: Session, user_id: int, study_type: str, energy: int):
    today = datetime.now().date()
    
    # PostgreSQL 전용 UPSERT 쿼리
    stmt = insert(DailyStudySummary).values(
        user_id=user_id,
        study_date=today,
        type=study_type,
        total_energy=energy,
        total_count=1
    )
    
    # 이미 해당 날짜/타입 데이터가 있으면 기존 값에 더하기
    stmt = stmt.on_conflict_do_update(
        index_elements=['user_id', 'study_date', 'type'], # 컬럼 리스트 지정
        set_={
            "total_energy": DailyStudySummary.total_energy + energy,
            "total_count": DailyStudySummary.total_count + 1
        }
    )
    
    db.execute(stmt)