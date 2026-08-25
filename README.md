# 🚀 VIPA Backend

## 프로젝트 개요

VIPA 애플리케이션의 핵심 API 서버로, 사용자 인증, 어휘 관리, 학습 데이터 처리 등 모든 비즈니스 로직을 담당합니다. 
FastAPI 기반의 고성능 RESTful API로 구성되어 있으며, 모바일 및 웹 클라이언트와 통신합니다.

---

## 🛠️ 기술 스택

| 항목 | 버전/도구 |
|------|---------|
| **언어** | Python 3.9+ |
| **프레임워크** | FastAPI |
| **ORM** | SQLAlchemy |
| **데이터베이스** | SQLite (개발) / PostgreSQL (프로덕션) |
| **서버** | Uvicorn |
| **검증** | Pydantic |
| **인증** | JWT (Bearer Token) |

---

## 🎯 핵심 기능

### 1. 사용자 인증 & 계정 관리
- **회원가입**: 이메일 기반 회원가입 (비밀번호 해싱)
- **로그인**: JWT 토큰 발급 (Access Token / Refresh Token)
- **프로필 관리**: 사용자 정보 조회 및 수정

### 2. 어휘 학습 시스템
- **어휘 CRUD**: 등록, 조회, 수정, 삭제
- **카테고리 관리**: 어휘를 주제별로 분류
- **검색 & 필터링**: 난이도, 카테고리 등으로 필터링

### 3. 학습 이력 추적
- **학습 기록 저장**: 사용자의 학습 활동 로깅
- **진도율 계산**: 사용자별 학습 진행도 통계
- **분석 데이터 제공**: 학습 성과 분석용 데이터 제공

---

## 🚀 시작하기

### 1. 환경 설정
```bash
# 저장소 클론
git clone https://github.com/VipaForENG/Vipa_backend.git
cd Vipa_backend

# 가상 환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 서버 실행
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. API 문서 확인
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📋 환경 변수 설정

`.env` 파일을 프로젝트 루트에 생성하고 다음 설정을 추가하세요:

```env
# 데이터베이스
# DATABASE_URL=postgresql://user:password@localhost/dbname

# JWT 설정
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# =================================================================
# Open AI API KEY
# =================================================================
OPENAI_API_KEY="your openAI_API_KEY"

# =================================================================
# (Gmail SMTP)
# =================================================================
MAIL_USERNAME="Your email"
MAIL_PASSWORD="your google app password"
MAIL_FROM="your email"
MAIL_PORT=587
MAIL_SERVER="smtp.gmail.com"
MAIL_STARTTLS=True
MAIL_SSL_TLS=False

```

---

## 🔐 보안

- ✅ **비밀번호 해싱**: Bcrypt를 사용한 안전한 비밀번호 저장
- ✅ **JWT 인증**: Bearer Token 기반 인증
- ✅ **CORS 설정**: 신뢰할 수 있는 도메인만 허용
- ✅ **입력 검증**: Pydantic을 통한 자동 스키마 검증

---

## 🧪 테스트

```bash
# pytest 실행
pytest

# 커버리지 리포트 생성
pytest --cov=app --cov-report=html
```

---

## 📞 문제 해결

| 문제 | 해결 방법 |
|------|---------|
| `ModuleNotFoundError` | `pip install -r requirements.txt` 재실행 |
| 데이터베이스 연결 오류 | `.env` 파일의 `DATABASE_URL` 확인 |
| JWT 토큰 만료 | Refresh Token을 사용하여 새 Access Token 발급 |

---

## 📝 개발 가이드

### 새 엔드포인트 추가 방법

1. **Schema 정의** (`app/schemas/new_schema.py`)
2. **Model 생성** (`app/models/new_model.py`)
3. **CRUD 로직** (`app/crud/new_crud.py`)
4. **API 라우터** (`app/api/v1/api/new_route.py`)
5. main.py에 라우터 등록

