import os
import sys
import pandas as pd
from sqlalchemy import create_engine

# =========================================================================
# [시스템 경로 최적화] 
# 스크립트가 위치한 backend/scripts 폴더의 상위 개념인 backend 폴더를 리눅스/윈도우 
# 환경 변수에 강제 등록합니다. 이를 통해 app.core.config 등 글로벌 모듈을 정상 참조합니다.
# =========================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.dirname(CURRENT_DIR)
sys.path.append(BACKEND_ROOT)

# 프로젝트 인프라 설정 및 DB URL 설정 가로채기
try:
    from app.core.config import settings
    # 프로젝트 글로벌 설정 객체에 등록된 실제 PostgreSQL 연결 주소 바인딩
    DATABASE_URL = settings.DATABASE_URL
except Exception as e:
    print(f"⚠️  주의: 글로벌 프로젝트 환경 변수 로드 실패 ({e})")
    print("▶ 로컬 개발용 기본 PostgreSQL 계정 정보로 대체 엔진을 빌드합니다.")
    # 모듈 참조 예외 발생 시 구동할 로컬 샌드박스 DB 기본 URL 포맷
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/vipa_db"

# ==========================================
# [설정 항목] 파일 소스 및 타겟 엔티티 정의
# ==========================================
CSV_FILE_PATH = os.path.join(BACKEND_ROOT, "data", "processed", "vipa_cefr_cleaned_dataset.csv")
TABLE_NAME = "vocabulary"  # SQLAlchemy 모델에 매핑된 마스터 테이블 엔티티 명칭


def run_vocabulary_migration():
    """
    서버에서 정제 및 target_word 추출 공정을 마친 CSV 파일을 
    로컬 시스템의 PostgreSQL 마스터 테이블에 벌크(Bulk) 방식으로 고속 주입하는 핵심 함수입니다.
    """
    print("==================================================")
    print("🔄 VIPA 로컬 데이터베이스 데이터 이식 파이프라인 가동")
    print("==================================================")

    # 1. 대상 CSV 인프라 정적 검증
    if not os.path.exists(CSV_FILE_PATH):
        print(f"❌ 치명적 오류: 지정된 경로에 정제 완료된 CSV 파일이 누락되었습니다.")
        print(f"▶ 탐색 실패 경로: {CSV_FILE_PATH}")
        print("💡 팁: 깃허브에서 pull을 정상적으로 받았는지, 혹은 경로가 올바른지 확인하세요.")
        return

    print(f"① 고품질 정제 데이터셋 파일 파싱 개시... \n▶ 대상 경로: {CSV_FILE_PATH}")
    
    # 인코딩 깨짐을 방지하기 위해 utf-8-sig 포맷으로 안전하게 데이터프레임 적재
    df = pd.read_csv(CSV_FILE_PATH, encoding="utf-8-sig")
    print(f"▶ 파싱 성공. 파이프라인 주입 대상 데이터 총합: {len(df):,} 개 문장")

    # 2. 데이터 유효성 방어선 구축 및 필터링
    # DB 스키마 제약조건(nullable=False)이 걸려있는 필수 필드가 비어있을 경우 원천 차단합니다.
    df = df.dropna(subset=["target_word", "cefr_level"])
    
    # 3. 데이터베이스 컬럼 동기화 가이드 검증
    # 서버 전처리 공정에서 컬럼 가이드를 맞췄으나, 혹시 모를 에러 방지를 위해 타겟 필드만 명시적 추출
    required_db_columns = ["target_word", "cefr_level", "expression", "meaning"]
    
    # 실제 데이터베이스에 주입할 최적화된 서브 셋 데이터프레임 빌드
    final_migration_df = df[required_db_columns]

    # 4. SQLAlchemy 로컬 연산 데이터베이스 커넥션 엔진 빌드
    engine = create_engine(DATABASE_URL)

    # 5. Pandas 내장 고속 다중 로우 매핑(Bulk Insert) 엔진 구동
    print(f"② 로컬 PostgreSQL [{TABLE_NAME}] 테이블 대상 초고속 벌크 적재 시작...")
    try:
        final_migration_df.to_sql(
            name=TABLE_NAME,
            con=engine,
            if_exists="append",  # 기존 마스터 테이블 뼈대를 유지하고 하단에 데이터를 누적 적재
            index=False,         # 판다스 데이터프레임 고유의 인덱스 번호는 DB 컬럼에 주입 제외
            method="multi",      # 복수 로우 바인딩 기술을 적용하여 커밋 횟수를 줄이고 가속 성능 확보
            chunksize=1000       # 1,000개 로우 단위로 블록 분할 커밋을 시행하여 로컬 메모리 과부하 방지
        )
        
        print("==================================================")
        print(f"🏆 [마이그레이션 성공] 총 {len(final_migration_df):,} 개의 데이터가 안정적으로 이식되었습니다.")
        print("==================================================")

    except Exception as e:
        print(f"❌ [마이그레이션 실패] 데이터베이스 적재 중 치명적 예외 발생")
        print(f"▶ 상세 에러 리포트: {e}")
        print("💡 해결 가이드: 데이터베이스에 이미 동일한 스키마 제약조건 충돌이 있는지 확인하세요.")


if __name__ == "__main__":
    run_vocabulary_migration()
