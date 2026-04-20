from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import date

async def get_daily_token_usage(db: AsyncSession, user_id: int, target_date: date) -> int:
    """
    특정 유저의 오늘 'CONVERSATION' 토큰 사용량을 조회합니다.
    """
    query = text("""
        SELECT used_tokens
        FROM daily_study_summary
        WHERE user_id = :user_id
          AND study_date = :target_date
          AND type = 'CONVERSATION'
    """)
    
    result = await db.execute(query, {
        "user_id": user_id, 
        "target_date": target_date
    })
    row = result.fetchone()
    
    # 기록이 있으면 해당 값 반환, 없으면 0 반환
    return row[0] if row else 0


async def update_daily_token_usage(db: AsyncSession, user_id: int, target_date: date, tokens_to_add: int) -> None:
    """
    사용된 토큰을 오늘의 'CONVERSATION' 기록에 누적(Upsert)합니다.
    설계하신 UNIQUE(user_id, study_date, type) 제약조건을 활용합니다.
    """
    # 핵심: ON CONFLICT를 사용하여 데이터 무결성을 보장하며 합산합니다.
    query = text("""
        INSERT INTO daily_study_summary (user_id, study_date, type, used_tokens)
        VALUES (:user_id, :target_date, 'CONVERSATION', :tokens_to_add)
        ON CONFLICT (user_id, study_date, type)
        DO UPDATE SET 
            used_tokens = daily_study_summary.used_tokens + EXCLUDED.used_tokens
    """)
    
    await db.execute(query, {
        "user_id": user_id,
        "target_date": target_date,
        "tokens_to_add": tokens_to_add
    })
    
    # 트랜잭션 확정
    await db.commit()