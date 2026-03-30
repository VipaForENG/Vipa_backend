# 🚀 VIPA Backend (FastAPI)

VIPA 애플리케이션의 인증 및 데이터 처리를 담당하는 백엔드 서버입니다.

## 🛠️ 기술 스택
- **Framework:** FastAPI
- **Language:** Python 3.9+
- **Database:** SQLite (개발용) / SQLAlchemy (ORM)
- **Server:** Uvicorn

# 🚀 VIPA Backend (FastAPI)

VIPA 애플리케이션의 데이터 처리 및 비즈니스 로직을 담당하는 백엔드 서버입니다.

## 📂 Project Structure & Directory Roles

`app` 디렉토리 내 주요 파일 및 폴더의 역할입니다.

```text
app/
├── main.py              # 애플리케이션 진입점 (FastAPI 인스턴스 생성 및 라우터 등록)
├── database.py          # DB 연결 설정 (SQLAlchemy Engine, SessionLocal 설정)
├── models/              # DB 테이블 정의 (SQLAlchemy 모델 파일들)
├── schemas/             # 데이터 검증 및 직렬화 (Pydantic 모델, Request/Response 규격)
├── crud/                # 데이터베이스 CRUD 로직 (DB 직접 조작 함수 모음)
├── api/                 # API 엔드포인트 라우터 (v1, v2 등 버전별 라우팅)
│   └── routes/           # 실제 기능별 API 경로 (users.py, vocab.py 등)
└── core/                # 공통 설정 (보안, JWT 설정, 환경 변수 로드 등)
