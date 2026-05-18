import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine

# =========================================================================
# [시스템 경로 및 환경 변수 최적화] 
# 🌟 [핵심 수정 1]: app.core.config를 불러오기 전에 .env 파일을 최우선으로 로드합니다.
# 이렇게 해야 FastAPI의 settings 객체가 공란이 되지 않고 .env의 실제 DATABASE_URL을 정상적으로 읽습니다.
# =========================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.dirname(CURRENT_DIR)
sys.path.append(BACKEND_ROOT)

env_path = Path(BACKEND_ROOT) / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# 프로젝트 인프라 설정 및 DB URL 설정 가로채기
try:
    from app.core.config import settings
    if hasattr(settings, "DATABASE_URL") and settings.DATABASE_URL:
        DATABASE_URL = str(settings.DATABASE_URL)
    else:
        raise ValueError("settings.DATABASE_URL 변수가 정의되지 않았거나 비어있습니다.")
except Exception as e:
    print(f"⚠️  주의: 글로벌 프로젝트 환경 변수 로드 실패 또는 빈 값 검출 ({e})")
    print("▶ 로컬 개발용 기본 PostgreSQL 계정 정보로 대체 엔진을 빌드합니다.")
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/vipa_db"

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ==========================================
# [설정 항목] 파일 소스 및 타겟 엔티티 정의
# ==========================================
CSV_FILE_PATH = os.path.join(BACKEND_ROOT, "data", "processed", "vipa_cefr_cleaned_dataset.csv")
TABLE_NAME = "vocabulary"


def run_vocabulary_migration():
    """
    서버에서 정제된 CSV 파일을 로컬 DB 구조(8개 컬럼 사양)에 100% 일치시켜 
    PostgreSQL 마스터 테이블에 벌크 적재하는 함수입니다.
    """
    print("==================================================")
    print("🔄 VIPA 로컬 데이터베이스 데이터 이식 파이프라인 가동")
    print("==================================================")

    # 1. 대상 CSV 인프라 정적 검증
    if not os.path.exists(CSV_FILE_PATH):
        print(f"❌ 치명적 오류: 지정된 경로에 정제 완료된 CSV 파일이 누락되었습니다.")
        print(f"▶ 탐색 실패 경로: {CSV_FILE_PATH}")
        return

    print(f"① 고품질 정제 데이터셋 파일 파싱 개시... \n▶ 대상 경로: {CSV_FILE_PATH}")
    df = pd.read_csv(CSV_FILE_PATH, encoding="utf-8-sig")
    print(f"▶ 파싱 성공. 파이프라인 주입 대상 데이터 총합: {len(df):,} 개 문장")

    # 2. 데이터 유효성 방어선 구축 (필수 필드 Null 값 원천 제거)
    df = df.dropna(subset=["target_word", "cefr_level"])
    
    # 3. [스키마 동기화]: DB 컬럼 가이드에 맞춰 데이터프레임 구조 확장
    print("② 로컬 DB 스키마 제약조건 동기화 및 누락 컬럼 기본값 매핑 중...")
    required_db_columns = ["target_word", "cefr_level", "expression", "meaning"]
    final_migration_df = df[required_db_columns].copy()

    # DB 테이블의 8개 컬럼 스펙에 맞추기 위해 누락된 필드들을 명시적으로 추가
    final_migration_df["test_id"] = None          
    final_migration_df["focus_point"] = None      
    final_migration_df["is_customized"] = False   

    # 4. SQLAlchemy 로컬 연산 데이터베이스 커넥션 엔진 빌드 (한글 윈도우 인코딩 방어)
    engine = create_engine(DATABASE_URL, connect_args={"client_encoding": "utf8"})

    # 5. Pandas 내장 고속 다중 로우 매핑(Bulk Insert) 엔진 구동
    print(f"③ 로컬 PostgreSQL [{TABLE_NAME}] 테이블 대상 초고속 벌크 적재 시작...")
    try:
        final_migration_df.to_sql(
            name=TABLE_NAME,
            con=engine,
            if_exists="append",  # 기존 마스터 테이블 데이터 밑에 누적 적재
            index=False,         # 판다스 인덱스는 DB 컬럼에서 제외
            method="multi",      # 복수 로우 바인딩 기술로 성능 가속
            chunksize=1000       # 1,000개 로우 단위 분할 커밋으로 메모리 안정성 확보
        )
        
        print("==================================================")
        print(f"🏆 [마이그레이션 성공] 총 {len(final_migration_df):,} 개의 데이터가 안정적으로 이식되었습니다.")
        print("==================================================")

    except Exception as e:
        print(f"❌ [마이그레이션 실패] 데이터베이스 적재 중 치명적 예외 발생")
        # 🌟 [핵심 수정 2]: 에러 메시지 출력 시 문자열 인코딩 충돌로 터지는 현상을 repr()로 원천 차단
        try:
            print(f"▶ 상세 에러 리포트 (Raw): {repr(e)}")
        except Exception as encode_err:
            print(f"▶ 상세 에러 리포트: 데이터베이스 연결 실패 또는 제약조건 위반 (인코딩 오류 내부 코드: {encode_err})")


if __name__ == "__main__":
    run_vocabulary_migration()