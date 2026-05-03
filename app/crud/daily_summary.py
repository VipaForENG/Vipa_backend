# app/crud/daily_summary.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from sqlalchemy.dialects.postgresql import insert
from datetime import date, datetime, timedelta
from fastapi import HTTPException, status

from app.models.user import User
from app.models.summary import DailyStudySummary

class CRUDDailySummary:
    
    # ---------------------------------------------------------
    # 1. 토큰 업데이트 (기존 crud_daily_summary.py)
    # ---------------------------------------------------------
    async def update_daily_token_usage(self, db: AsyncSession, user_id: int, target_date: date, tokens_to_add: int) -> None:
        """사용된 대화 토큰을 누적 저장합니다."""
        query = text("""
            INSERT INTO daily_study_summary (user_id, study_date, type, used_tokens)
            VALUES (:user_id, :target_date, 'CONVERSATION', :tokens_to_add)
            ON CONFLICT (user_id, study_date, type)
            DO UPDATE SET 
                used_tokens = daily_study_summary.used_tokens + EXCLUDED.used_tokens
        """)
        await db.execute(query, {
            "user_id": user_id, "target_date": target_date, "tokens_to_add": tokens_to_add
        })
        await db.commit()

    # ---------------------------------------------------------
    # 2. 에너지 업데이트 (기존 summary.py)
    # ---------------------------------------------------------
    async def update_daily_energy(self, db: AsyncSession, user_id: int, study_type: str, energy: int) -> None:
        """학습 종료 시 에너지를 누적 저장합니다."""
        today = datetime.now().date()
        stmt = insert(DailyStudySummary).values(
            user_id=user_id, study_date=today, type=study_type, total_energy=energy, total_count=1
        ).on_conflict_do_update(
            index_elements=['user_id', 'study_date', 'type'],
            set_={
                "total_energy": DailyStudySummary.total_energy + energy,
                "total_count": DailyStudySummary.total_count + 1
            }
        )
        await db.execute(stmt)
        await db.commit()

    # ---------------------------------------------------------
    # 3. 연속 출석 계산 로직 (내부 호출용)
    # ---------------------------------------------------------
    async def calculate_continuous_attendance(self, db: AsyncSession, user_id: int) -> int:
        """연속 출석 일수(스트릭)를 계산합니다."""
        stmt = select(DailyStudySummary.study_date)\
            .filter(DailyStudySummary.user_id == user_id)\
            .distinct()\
            .order_by(DailyStudySummary.study_date.desc())
        
        result = await db.execute(stmt)
        date_list = result.scalars().all() # 비동기 쿼리 결과 리스트화

        if not date_list:
            return 0
        
        today = date.today()
        yesterday = today - timedelta(days=1)
        last_study_date = date_list[0]
        
        if last_study_date < yesterday:
            return 0
        
        streak = 0
        current_check_date = last_study_date
        
        for study_date in date_list:
            if study_date == current_check_date:
                streak += 1
                current_check_date -= timedelta(days=1)
            else:
                break
                
        return streak

    # ---------------------------------------------------------
    # 4. 홈 화면 요약 통계 조회 (기존 log.py 통합 및 비동기 전환)
    # ---------------------------------------------------------
    async def get_home_summary(self, db: AsyncSession, user_id: int) -> dict:
        """홈 화면에 필요한 주간 에너지, 출석, 유저 정보를 반환합니다."""
        
        # [4-1. 유저 조회] (비동기 변환)
        user_stmt = select(User).where(User.user_id == user_id)
        user = (await db.execute(user_stmt)).scalars().first()
        
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="유저를 찾을 수 없습니다.")

        # [4-2. 랭킹 및 상위 % 계산] (비동기 변환)
        total_stmt = select(func.count(User.user_id))
        total_users = (await db.execute(total_stmt)).scalar() or 0
        
        rank_stmt = select(func.count(User.user_id)).where(User.study_count > user.study_count)
        rank_higher = (await db.execute(rank_stmt)).scalar() or 0
        rank = rank_higher + 1
        
        top_percent = round((rank / total_users) * 100, 1) if total_users > 0 else 100.0

        # [4-3. 최근 7일 막대 그래프 데이터]
        today_date = datetime.now().date()
        seven_days_ago = today_date - timedelta(days=6)
        
        logs_stmt = select(DailyStudySummary).where(
            DailyStudySummary.user_id == user_id,
            DailyStudySummary.study_date >= seven_days_ago
        )
        summary_logs = (await db.execute(logs_stmt)).scalars().all()

        weekly_data = []
        for i in range(6, -1, -1):
            target_date = today_date - timedelta(days=i)
            
            conv = next((s for s in summary_logs if s.study_date == target_date and s.type == "CONVERSATION"), None)
            vocab = next((s for s in summary_logs if s.study_date == target_date and s.type == "VOCABULARY"), None)
            
            conv_energy = conv.total_energy if conv else 0
            vocab_energy = vocab.total_energy if vocab else 0
            
            weekly_data.append({
                "date": str(target_date),
                "conv_energy": conv_energy,
                "vocab_energy": vocab_energy,
                "total_energy": conv_energy + vocab_energy
            })

        # [4-4. 이번 주 출석체크] - 날짜 비교 오류 해결 (.isoformat 제거)
        start_of_week = today_date - timedelta(days=today_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        att_stmt = select(DailyStudySummary.study_date).where(
            DailyStudySummary.user_id == user_id,
            DailyStudySummary.study_date >= start_of_week,
            DailyStudySummary.study_date <= end_of_week
        ).distinct()
        attendance_data = (await db.execute(att_stmt)).scalars().all()

        continuous_attendance = await self.calculate_continuous_attendance(db, user_id)

        days_map = {0: "월", 1: "화", 2: "수", 3: "목", 4: "금", 5: "토", 6: "일"}
        attended_indices = sorted(list(set([d.weekday() for d in attendance_data])))
        attendance = [days_map[idx] for idx in attended_indices]

        # [4-5. 티어 계산 헬퍼 함수]
        def calculate_tier(count: int) -> str:
            if count < 50: return "BRONZE"
            if count < 150: return "SILVER"
            return "GOLD"

        # [4-6. 최종 반환]
        return {
            "nickname": user.nickname,
            "tier": calculate_tier(user.study_count),
            "top_percent": top_percent,
            "weekly_data": weekly_data,      
            "attendance": attendance,        
            "continuous_attendance_count": continuous_attendance,
            "study_achievement_rate": 90     
        }

daily_summary_crud = CRUDDailySummary()