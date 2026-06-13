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
        dates = (await db.execute(stmt)).scalars().all()
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

        total_learning_count = int((
            await db.execute(
                select(func.coalesce(func.sum(StudyLog.earned_energy), 0))
                .where(StudyLog.user_id == user_id)
            )
        ).scalar() or 0)
        type_totals = (
            await db.execute(
                select(
                    StudyLog.type,
                    func.coalesce(func.sum(StudyLog.earned_energy), 0).label("total"),
                )
                .where(StudyLog.user_id == user_id)
                .group_by(StudyLog.type)
            )
        ).all()
        vocabulary_learning_count = next(
            (int(row.total) for row in type_totals if row.type == "VOCABULARY"),
            0,
        )
        conversation_learning_count = next(
            (int(row.total) for row in type_totals if row.type == "CONVERSATION"),
            0,
        )

        total_users = int((
            await db.execute(select(func.count(User.user_id)))
        ).scalar() or 0)
        learning_totals = (
            select(
                StudyLog.user_id.label("user_id"),
                func.sum(StudyLog.earned_energy).label("total"),
            )
            .group_by(StudyLog.user_id)
            .subquery()
        )
        rank_higher = int((
            await db.execute(
                select(func.count()).select_from(learning_totals).where(
                    learning_totals.c.total > total_learning_count
                )
            )
        ).scalar() or 0)
        top_percent = (
            round(((rank_higher + 1) / total_users) * 100, 1)
            if total_users > 0
            else 100.0
        )

        today = date.today()
        seven_days_ago = today - timedelta(days=6)
        log_date = func.date(StudyLog.created_at + text("INTERVAL '9 hours'"))
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
                (
                    int(row.total_energy)
                    for row in rows
                    if row.study_date == target_date and row.type == "CONVERSATION"
                ),
                0,
            )
            vocabulary = next(
                (
                    int(row.total_energy)
                    for row in rows
                    if row.study_date == target_date and row.type == "VOCABULARY"
                ),
                0,
            )
            weekly_data.append({
                "date": str(target_date),
                "conv_energy": conversation,
                "vocab_energy": vocabulary,
                "total_energy": conversation + vocabulary,
            })

        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        attendance_dates = (
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

        day_names = ["월", "화", "수", "목", "금", "토", "일"]
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
            if maximum is None or total_learning_count < maximum:
                tier = name
                achievement_rate = (
                    100
                    if maximum is None
                    else round(
                        (total_learning_count - minimum)
                        / (maximum - minimum)
                        * 100
                    )
                )
                break

        return {
            "nickname": user.nickname or "사용자",
            "tier": tier,
            "top_percent": top_percent,
            "total_learning_count": total_learning_count,
            "today_vocabulary_count": vocabulary_learning_count,
            "today_conversation_count": conversation_learning_count,
            "weekly_data": weekly_data,
            "attendance": [day_names[item.weekday()] for item in attendance_dates],
            "attendance_dates": [str(item) for item in attendance_dates],
            "continuous_attendance_count": await self.calculate_continuous_attendance(
                db, user_id
            ),
            "study_achievement_rate": achievement_rate,
        }


daily_summary_crud = CRUDDailySummary()
