from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.user import User
from app.models.summary import DailyStudySummary  # 최적화를 위한 집계 모델 추가
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from datetime import date, timedelta


def calculate_continuous_attendance(db: Session, user_id: int) -> int:
    """
    사용자의 연속 출석 일수를 계산합니다.
    - 오늘 공부 기록이 있으면 오늘부터 카운트
    - 오늘 기록이 없어도 어제 기록이 있으면 어제까지의 스트릭 유지
    - 어제조차 기록이 없으면 스트릭 0
    """
    # 1. 유저의 모든 출석 날짜를 내림차순(최신순)으로 가져옵니다. (중복 제거)
    attendance_dates = db.query(DailyStudySummary.study_date)\
        .filter(DailyStudySummary.user_id == user_id)\
        .distinct()\
        .order_by(DailyStudySummary.study_date.desc())\
        .all()

    if not attendance_dates:
        return 0

    # SQLAlchemy 결과 객체에서 date 리스트로 변환
    date_list = [d.study_date for d in attendance_dates]
    
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # 마지막 학습일 확인
    last_study_date = date_list[0]
    
    # 어제조차 공부를 안 했다면 연속성 파괴 (0일)
    if last_study_date < yesterday:
        return 0
    
    # 오늘 아직 안 했어도 어제까지 했으면 어제부터 카운트 시작
    # 오늘 했으면 오늘부터 카운트 시작
    streak = 0
    current_check_date = last_study_date
    
    for study_date in date_list:
        if study_date == current_check_date:
            streak += 1
            current_check_date -= timedelta(days=1) # 하루 전 날짜로 업데이트
        else:
            # 날짜가 연속되지 않으면 루프 중단
            break
            
    return streak


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
    # 1. 명확하게 문자열로 변환하여 DB 비교 오류 원천 차단
    today_date = today_dt.date() if hasattr(today_dt, 'date') else today_dt
    
    # 이번 주 월요일과 일요일 날짜 계산
    start_of_week = today_date - timedelta(days=today_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    # DB 쿼리 시 날짜를 ISO 문자열('YYYY-MM-DD')로 변환하여 안전하게 대소 비교
    attendance_data = db.query(DailyStudySummary.study_date).filter(
        DailyStudySummary.user_id == user_id,
        DailyStudySummary.study_date >= start_of_week.isoformat(),
        DailyStudySummary.study_date <= end_of_week.isoformat() # 닫힌 구간으로 확실히 제한!
    ).distinct().all()

    continuous_attendance = calculate_continuous_attendance(db, user_id)

    # 2. 요일 정렬 버그 해결 (한글 정렬 대신 요일 인덱스(0~6)로 정렬)
    days_map = {0: "월", 1: "화", 2: "수", 3: "목", 4: "금", 5: "토", 6: "일"}
    
    # 출석한 날짜의 요일 인덱스(0~6)만 뽑아서 중복을 제거하고 정렬합니다.
    attended_indices = sorted(list(set([d.study_date.weekday() for d in attendance_data])))
    
    # 정렬된 인덱스를 다시 한국어 요일로 변환합니다.
    attendance = [days_map[idx] for idx in attended_indices]

    # --- [5. 최종 결과 반환] ---
    return {
        "nickname": user.nickname,
        "tier": calculate_tier(user.study_count),
        "top_percent": top_percent,
        "weekly_data": weekly_data,      
        "attendance": attendance,        # 이제 무조건 이번 주 데이터만, 월~일 순서대로 나옵니다!
        "continuous_attendance_count": continuous_attendance,
        "study_achievement_rate": 90     
    }

def calculate_tier(count: int) -> str:
    """학습 횟수에 따른 티어 결정 로직"""
    if count < 50: return "BRONZE"
    if count < 150: return "SILVER"
    return "GOLD"