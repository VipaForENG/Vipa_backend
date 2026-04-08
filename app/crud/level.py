from sqlalchemy.orm import Session
from app.models.level import UserLevel, LevelTestResult
from app.schemas.level import LevelTestDetail
from typing import Optional

def get_user_level(db: Session, user_id: int) -> Optional[UserLevel]:
    """
    [조회] 특정 유저의 현재 레벨 프로필을 조회합니다.
    
    Args:
        db (Session): 데이터베이스 세션
        user_id (int): 조회할 유저의 PK
        
    Returns:
        UserLevel 객체 (존재하지 않으면 None 반환)
    """
    return db.query(UserLevel).filter(UserLevel.user_id == user_id).first()


def create_or_update_user_level(db: Session, user_id: int, cefr_level: str, overall_score: float) -> UserLevel:
    """
    [생성/수정] 유저의 레벨을 업데이트하거나, 처음 테스트를 치른 경우 새로 생성합니다. (Upsert 로직)
    
    Args:
        db (Session): 데이터베이스 세션
        user_id (int): 유저 PK
        cefr_level (str): GPT가 판정한 최종 레벨 (예: "B2")
        overall_score (float): 종합 점수 (예: 85.5)
        
    Returns:
        업데이트 또는 생성된 UserLevel 객체
    """
    db_level = get_user_level(db, user_id)
    
    if db_level:
        # 1. 이미 레벨 정보가 있다면 값만 덮어씌웁니다. (재시험인 경우)
        db_level.cefr_level = cefr_level
        db_level.overall_score = overall_score
    else:
        # 2. 레벨 정보가 없다면 새로 레코드(행)를 생성합니다. (첫 시험인 경우)
        db_level = UserLevel(
            user_id=user_id,
            cefr_level=cefr_level,
            overall_score=overall_score
        )
        db.add(db_level)
        
    # 중요: commit() 대신 flush()를 사용하여 임시로 DB에 반영하고 user_level_id를 확보합니다.
    # (상세 결과 테이블에서 이 ID를 바로 외래키로 써야 하기 때문)
    db.flush()  
    return db_level


def create_test_result(db: Session, user_level_id: int, raw_analysis: dict, tags: str) -> LevelTestResult:
    """
    [생성] GPT-5가 분석한 상세 테스트 결과(JSON 프로필)를 이력(History)으로 저장합니다.
    
    Args:
        db (Session): 데이터베이스 세션
        user_level_id (int): UserLevel 테이블의 PK (외래키로 사용)
        raw_analysis (dict): GPT-5가 응답한 상세 JSON 데이터 (정답률, 문법 평가 등)
        tags (str): 주요 취약점 요약 태그 (예: "시제 혼동, 어휘 부족")
        
    Returns:
        생성된 LevelTestResult 객체
    """
    db_result = LevelTestResult(
        user_level_id=user_level_id,
        raw_analysis_json=raw_analysis, # JSONB 컬럼에 파이썬 딕셔너리를 바로 넣습니다.
        weakness_tags=tags
    )
    db.add(db_result)
    db.commit() # 여기서 최종적으로 DB에 모든 변경사항을 확정(저장)합니다.
    db.refresh(db_result) # DB에서 생성된 시간(created_at) 등을 객체로 다시 불러옵니다.
    
    return db_result