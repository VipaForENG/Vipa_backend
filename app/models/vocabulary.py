from typing import Optional
from sqlalchemy import String, TEXT, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class Vocabulary(Base):
    """
    AI Hub 20만 건의 데이터셋을 적재하는 마스터 테이블입니다.
    Mapped[타입] 지정을 통해 Pylance가 필드의 정적 타입을 명확히 인지하도록 구조를 개선했습니다.
    """
    __tablename__ = "vocabulary"

    # mapped_column을 활용하여 각 컬럼의 자료형을 명시적 파이썬 프리미티브 타입과 바인딩합니다.
    vocab_id: Mapped[int] = mapped_column(primary_key=True)
    target_word: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # 고속 Fetching을 위한 인덱스 지정 구조 유지
    cefr_level: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    
    # Null 허용 필드는 Optional[자료형]을 사용하여 안전하게 매핑합니다.
    test_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    expression: Mapped[Optional[str]] = mapped_column(TEXT, nullable=True)
    meaning: Mapped[Optional[str]] = mapped_column(TEXT, nullable=True)
    focus_point: Mapped[Optional[str]] = mapped_column(TEXT, nullable=True)
    is_customized: Mapped[bool] = mapped_column(Boolean, default=False)

    # 다중 조건 검색 가속을 위한 복합 인덱스 제어권 보존
    __table_args__ = (
        Index("idx_vocab_cefr_word", "cefr_level", "target_word"),
    )