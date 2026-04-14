from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.user import User
from app.models.summary import DailyStudySummary  # 최적화를 위한 집계 모델 추가
from datetime import datetime, timedelta
from fastapi import HTTPException, status

def get_home_summary(db: Session, user_id: int):
    """
    홈 화면에 필요한 모든 정보를 집계 테이블(DailyStudySummary)을 통해 초고속으로 반환합니다.
    1. 유저 정보 및 랭킹 (User 테이블 기준)
    2. 최근 7일간의 학습 에너지 통계 (집계 테이블 활용)
    3. 이번 주 출석 현황 (집계 테이블 날짜 기준)
    """

    # --- [1. 유저 조회 및 예외 처리] ---
    user = db.query(User).filter(User.user_id == user_id).first()
    
    # Pylance 에러 방지 및 유저 존재 여부 확인
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 유저를 찾을 수 없습니다."
        )

    # --- [2. 랭킹 및 상위 % 계산] ---
    # 전체 유저 수와 내 등수를 계산하여 상위 % 산출
    total_users = db.query(User).count()
    rank = db.query(User).filter(User.study_count > user.study_count).count() + 1
    top_percent = round((rank / total_users) * 100, 1) if total_users > 0 else 100.0

    # --- [3. 최근 7일 막대 그래프 데이터 (집계 테이블 조회)] ---
    today_dt = datetime.now()
    today_date = today_dt.date()
    seven_days_ago = today_date - timedelta(days=6)
    
    # [최적화 핵심] StudyLog가 아닌, 이미 계산된 DailyStudySummary에서 7일치만 가져옴
    summary_logs = db.query(DailyStudySummary).filter(
        DailyStudySummary.user_id == user_id,
        DailyStudySummary.study_date >= seven_days_ago
    ).all()

    # 데이터가 없는 날도 0으로 채워서 7개의 막대 데이터를 만듦
    weekly_data = []
    for i in range(6, -1, -1):
        target_date = today_date - timedelta(days=i)
        
        # 해당 날짜의 타입별(회화/어휘) 에너지를 집계 리스트에서 탐색
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

    # --- [4. 이번 주 출석체크 (월~일)] ---
    # 이번 주 월요일 날짜 계산 (datetime.weekday()는 월요일이 0)
    start_of_week = today_date - timedelta(days=today_dt.weekday())
    
    # 이번 주에 기록이 있는 날짜들을 중복 없이 가져옴
    attendance_data = db.query(DailyStudySummary.study_date).filter(
        DailyStudySummary.user_id == user_id,
        DailyStudySummary.study_date >= start_of_week
    ).distinct().all()

    # 요일 맵핑 (Python weekday(): 0=월, 1=화, ..., 6=일)
    days_map = {0: "월", 1: "화", 2: "수", 3: "목", 4: "금", 5: "토", 6: "일"}
    
    # 기록된 날짜들을 한국어 요일 리스트로 변환 (중복 제거 및 정렬)
    attendance = sorted(list(set([days_map[d.study_date.weekday()] for d in attendance_data])))

    # --- [5. 최종 결과 반환] ---
    return {
        "nickname": user.nickname,
        "tier": calculate_tier(user.study_count),
        "top_percent": top_percent,
        "weekly_data": weekly_data,      # 최적화된 에너지 밸런스 데이터
        "attendance": attendance,        # 요일별 출석 리스트
        "study_achievement_rate": 90     # 목표 달성률 (추후 로직 고도화 가능)
    }

def calculate_tier(count: int) -> str:
    """학습 횟수에 따른 티어 결정 로직"""
    if count < 50: return "BRONZE"
    if count < 150: return "SILVER"
    return "GOLD"