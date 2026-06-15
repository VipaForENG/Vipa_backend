from datetime import date, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.study_log import StudyLog
from app.models.summary import DailyStudySummary
from app.models.user import User


class CRUDDailySummary:
    async def update_daily_token_usage(
        self,
        db: AsyncSession,
        user_id: int,
        target_date: date,
        tokens_to_add: int,
    ) -> None:
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
            "tokens_to_add": tokens_to_add,
        })
        await db.commit()

    async def update_daily_energy(
        self,
        db: AsyncSession,
        user_id: int,
        study_type: str,
        energy: int,
    ) -> None:
        stmt = insert(DailyStudySummary).values(
            user_id=user_id,
            study_date=datetime.now().date(),
            type=study_type,
            total_energy=energy,
            total_count=1,
        ).on_conflict_do_update(
            index_elements=["user_id", "study_date", "type"],
            set_={
                "total_energy": DailyStudySummary.total_energy + energy,
                "total_count": DailyStudySummary.total_count + 1,
            },
        )
        await db.execute(stmt)
        await db.commit()

    async def calculate_continuous_attendance(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> int:
        log_date = func.date(StudyLog.created_at + text("INTERVAL '9 hours'"))
        stmt = (
            select(log_date)
            .where(StudyLog.user_id == user_id)
            .distinct()
            .order_by(log_date.desc())
        )
        raw_dates = (await db.execute(stmt)).scalars().all()
        
        # 🔥 방어 로직: DB에서 꺼낸 날짜가 문자열일 경우를 대비해 변환
        dates = []
        for d in raw_dates:
            if isinstance(d, str):
                dates.append(datetime.strptime(d, "%Y-%m-%d").date())
            elif isinstance(d, datetime):
                dates.append(d.date())
            else:
                dates.append(d)

        if not dates or dates[0] < date.today() - timedelta(days=1):
            return 0

        streak = 0
        expected = dates[0]
        for study_date in dates:
            if study_date != expected:
                break
            streak += 1
            expected -= timedelta(days=1)
        return streak

    async def get_home_summary(self, db: AsyncSession, user_id: int) -> dict:
        user = (
            await db.execute(select(User).where(User.user_id == user_id))
        ).scalars().first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다.",
            )

        # 🔥 문자열 날짜를 안전한 date 객체로 파싱하는 헬퍼 함수
        def to_date(d):
            if isinstance(d, str):
                return datetime.strptime(d, "%Y-%m-%d").date()
            if isinstance(d, datetime):
                return d.date()
            return d

        today = date.today()
        log_date = func.date(StudyLog.created_at + text("INTERVAL '9 hours'"))

        # 1. 누적 획득 에너지
        total_learning_energy = int((
            await db.execute(
                select(func.coalesce(func.sum(StudyLog.earned_energy), 0))
                .where(StudyLog.user_id == user_id)
            )
        ).scalar() or 0)

        # 2. 오늘 획득한 에너지
        today_type_totals = (
            await db.execute(
                select(
                    StudyLog.type,
                    func.coalesce(func.sum(StudyLog.earned_energy), 0).label("total_energy"),
                )
                .where(
                    StudyLog.user_id == user_id,
                    log_date == today  
                )
                .group_by(StudyLog.type)
            )
        ).all()
        
        vocabulary_energy = next(
            (int(row.total_energy) for row in today_type_totals if row.type == "VOCABULARY"), 0
        )
        conversation_energy = next(
            (int(row.total_energy) for row in today_type_totals if row.type == "CONVERSATION"), 0
        )

        # 3. 유저 랭킹
        total_users = int((
            await db.execute(select(func.count(User.user_id)))
        ).scalar() or 0)
        
        learning_totals = (
            select(
                StudyLog.user_id.label("user_id"),
                func.sum(StudyLog.earned_energy).label("total_energy"),
            )
            .group_by(StudyLog.user_id)
            .subquery()
        )
        rank_higher = int((
            await db.execute(
                select(func.count()).select_from(learning_totals).where(
                    learning_totals.c.total_energy > total_learning_energy
                )
            )
        ).scalar() or 0)
        
        top_percent = (
            round(((rank_higher + 1) / total_users) * 100, 1)
            if total_users > 0
            else 100.0
        )

        # 4. 주간 학습 그래프 (🔥 to_date 방어 로직 적용)
        seven_days_ago = today - timedelta(days=6)
        rows = (
            await db.execute(
                select(
                    log_date.label("study_date"),
                    StudyLog.type,
                    func.sum(StudyLog.earned_energy).label("total_energy"),
                )
                .where(
                    StudyLog.user_id == user_id,
                    log_date >= seven_days_ago,
                )
                .group_by(log_date, StudyLog.type)
            )
        ).all()

        weekly_data = []
        for days_ago in range(6, -1, -1):
            target_date = today - timedelta(days=days_ago)
            conversation = next(
                (int(row.total_energy) for row in rows if to_date(row.study_date) == target_date and row.type == "CONVERSATION"), 0
            )
            vocabulary = next(
                (int(row.total_energy) for row in rows if to_date(row.study_date) == target_date and row.type == "VOCABULARY"), 0
            )
            weekly_data.append({
                "date": str(target_date),
                "conv_energy": conversation,
                "vocab_energy": vocabulary,
                "total_energy": conversation + vocabulary,
            })

        # 5. 주간 출석부 (🔥 to_date 방어 로직 적용)
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        raw_attendance_dates = (
            await db.execute(
                select(log_date)
                .where(
                    StudyLog.user_id == user_id,
                    log_date >= start_of_week,
                    log_date <= end_of_week,
                )
                .distinct()
                .order_by(log_date)
            )
        ).scalars().all()

        # 꺼낸 데이터를 무조건 date 객체로 변환
        attendance_dates = [to_date(item) for item in raw_attendance_dates]

        day_names = ["월", "화", "수", "목", "금", "토", "일"]
        
        # 6. 티어 시스템
        tiers = [
            ("BRONZE", 0, 50),
            ("SILVER", 50, 150),
            ("GOLD", 150, 300),
            ("EMERALD", 300, 600),
            ("DIAMOND", 600, 1000),
            ("MASTER", 1000, None),
        ]
        tier = "MASTER"
        achievement_rate = 100
        for name, minimum, maximum in tiers:
            if maximum is None or total_learning_energy < maximum:
                tier = name
                achievement_rate = (
                    100
                    if maximum is None
                    else round(
                        (total_learning_energy - minimum)
                        / (maximum - minimum)
                        * 100
                    )
                )
                break

        return {
            "nickname": user.nickname or "사용자",
            "tier": tier,
            "top_percent": top_percent,
            "total_learning_energy": total_learning_energy,
            "today_vocabulary_energy": vocabulary_energy,
            "today_conversation_energy": conversation_energy,
            "weekly_data": weekly_data,
            "attendance": [day_names[item.weekday()] for item in attendance_dates],
            "attendance_dates": [str(item) for item in attendance_dates],
            "continuous_attendance_count": await self.calculate_continuous_attendance(db, user_id),
            "study_achievement_rate": achievement_rate,
        }

daily_summary_crud = CRUDDailySummary()