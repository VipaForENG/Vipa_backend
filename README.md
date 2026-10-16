# AI 기반 사용자 맞춤형 영어학습 어플 · 백엔드

**레벨 테스트 결과를 회화·시나리오·어휘 학습으로 연결한 팀 프로젝트입니다.**

2학년 1학기 융합프로젝트 실습에서 제작했습니다. 사용자별 영어 수준과 학습 기록을 저장하고, 해당 데이터를 활용해 AI 학습 콘텐츠를 제공하는 백엔드를 구현했습니다.

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=flat-square)

| 구분 | 내용 |
| :--- | :--- |
| 개발 형태 | 대학 수업 팀 프로젝트 |
| 담당자 | **엄유준 · DB 설계 및 백엔드 전체 개발** |
| 추가 담당 | Flutter 프론트엔드 초기 구조 구성 |
| 협업 범위 | 팀원이 UI·프론트엔드 구현 담당 |
| 앱 동작 확인 | 레벨 테스트 · 평가 결과 · 결과 기반 맞춤 시나리오 생성 및 회화 |

[프론트엔드 저장소](https://github.com/VipaForENG/Vipa_frontend) · [개인 GitHub](https://github.com/EddieEom)

## 실행 화면

<table>
<tr><th width="50%">① CEFR 레벨 테스트</th><th width="50%">② 레벨 평가 결과</th></tr>
<tr>
<td align="center"><img src="https://raw.githubusercontent.com/EddieEom/EddieEom/main/assets/screenshots/vipa-test.jpg" alt="문제를 제시하는 레벨 테스트 화면" width="240"/></td>
<td align="center"><img src="https://raw.githubusercontent.com/EddieEom/EddieEom/main/assets/screenshots/vipa-result.jpg" alt="B1 판정과 피드백을 표시하는 결과 화면" width="240"/></td>
</tr>
<tr><th>③ 맞춤 시나리오 생성</th><th>④ 실전 회화</th></tr>
<tr>
<td align="center"><img src="https://raw.githubusercontent.com/EddieEom/EddieEom/main/assets/screenshots/vipa-scenario.jpg" alt="선택한 상황의 시나리오를 생성하는 화면" width="240"/></td>
<td align="center"><img src="https://raw.githubusercontent.com/EddieEom/EddieEom/main/assets/screenshots/vipa-conversation.jpg" alt="생성한 시나리오로 회화를 진행하는 화면" width="240"/></td>
</tr>
</table>

위 화면은 팀에서 제작한 Flutter 앱입니다. 본인은 화면에 필요한 DB·API·AI 연동을 담당했습니다.

## 직접 구현한 부분

| 영역 | 구현 내용 |
| :--- | :--- |
| DB 설계 | 사용자·레벨·대화·어휘·학습 이력 테이블과 관계 구성 |
| 인증·사용자 | JWT 인증, 회원 정보 관리, 소셜 로그인 및 비밀번호 복구 API |
| 레벨 테스트 | AI 문제 생성, 답변 분석, 현재 레벨과 테스트 결과 저장 |
| AI 회화 | 사용자 레벨과 최근 대화를 전달해 답변·번역·피드백 생성 |
| 실전 시나리오 | 상황별 회화 생성, 답변 평가, 단계별 힌트, 학습 결과 저장 |
| 어휘·학습 기록 | 신규·복습·오답 문제, 즐겨찾기, 학습 내역과 홈 요약 API |
| 파일 연동 | Supabase Storage를 활용한 프로필 이미지·회화 녹음 저장 |

## 설계할 때 신경 쓴 부분

### 1. 테스트 결과를 다음 학습에 활용

레벨 평가 결과를 저장한 뒤, 회화와 시나리오 생성 요청에 사용자 레벨을 전달했습니다. 테스트와 학습 기능이 같은 사용자 데이터를 활용하도록 연결했습니다.

### 2. 현재 상태와 과거 기록 분리

현재 레벨은 `user_levels`, 테스트별 분석 결과는 `level_test_results`에 저장했습니다. 대화도 세션과 턴을 나눠 저장해 학습 내용을 다시 조회할 수 있도록 구성했습니다.

### 3. AI 응답을 저장 가능한 데이터로 처리

AI에 레벨·피드백·교정 문장 등을 구조화된 JSON으로 요청하고, 백엔드에서 처리해 DB에 저장했습니다. 생성된 시나리오의 키워드와 예상 답변은 단계별 힌트에도 활용했습니다.

### 4. 화면과 서버의 역할 분리

Flutter는 화면과 사용자 입력을 처리하고, FastAPI는 인증·데이터 조회·AI 요청·학습 기록 저장을 담당했습니다. 팀원과 앱을 연결하며 요청·응답 형식을 맞췄습니다.

## 시스템 구성

| 구성 요소 | 역할과 연결 |
| :--- | :--- |
| Flutter 앱 | REST API로 서버에 요청, JWT로 사용자 인증 |
| FastAPI 서버 | 인증·학습 API, AI 요청, DB 조회·저장 |
| PostgreSQL | 사용자 정보와 레벨·대화·어휘·학습 이력 저장 |
| OpenAI API | 문제·시나리오·회화 생성, 답변 분석·평가 |
| Supabase Storage | 프로필 이미지·녹음 파일 저장, URL을 DB에서 관리 |

프로젝트를 진행하며 **관계형 DB 설계 → API 구현 → AI 연동 → 앱에서 결과 확인**까지 경험했습니다.

<details>
<summary><b>주요 기능과 API 영역</b></summary>

기본 경로는 `/api/v1`입니다.

| 영역 | 경로 | 주요 기능 |
| :--- | :--- | :--- |
| 사용자 | `/users` | 회원가입·로그인·프로필·비밀번호 관리 |
| 소셜 인증 | `/auth` | Google·Kakao 로그인 |
| 레벨 테스트 | `/level-test` | 문제 생성·답변 평가·레벨 저장 |
| 자유 회화 | `/chat` | 레벨 기반 AI 회화·피드백 |
| 실전 회화 | `/scenario` | 시나리오 생성·평가·힌트·녹음 업로드 |
| 상황 분류 | `/category` | 학습 상황·카테고리 조회 |
| 어휘 학습 | `/vocabulary` | 문제·정답 확인·즐겨찾기·오답 이력 |
| 회화 이력 | `/conversation` | 세션별 대화·교정 내용 조회 |
| 홈 | `/home` | 학습 요약 조회 |

실전 회화는 AI 9턴·사용자 8턴의 시나리오를 생성하도록 구성했습니다. 힌트는 키워드, 문장 시작 부분, 예상 답변 전체의 3단계로 제공합니다.

</details>

<details>
<summary><b>DB와 코드 구성</b></summary>

| 데이터 영역 | 주요 테이블 |
| :--- | :--- |
| 사용자·레벨 | `users`, `user_levels`, `level_test_results` |
| 상황 분류 | `main_category`, `sub_category` |
| 시나리오·회화 | `custom_scenario`, `conversation_session`, `conversation_turn`, `sentence_log` |
| 학습 집계 | `study_log`, `daily_study_summary` |
| 어휘 | `vocabulary`, `vocabulary_study`, `vocab_learning_detail` |

| 폴더 | 역할 |
| :--- | :--- |
| `app/routes`, `app/api` | API 요청 처리 |
| `app/models`, `app/schemas` | DB 모델과 요청·응답 형식 |
| `app/crud`, `app/services` | 데이터 접근과 기능 처리 |
| `app/core` | DB·인증·AI·메일·Storage 설정 |
| `alembic` | DB 마이그레이션 |

기능에 따라 SQLAlchemy의 동기 세션과 비동기 세션을 함께 사용합니다. 비동기 PostgreSQL 연결에는 `asyncpg`를 사용합니다.

</details>

<details>
<summary><b>설치 및 실행</b></summary>

### 1. 저장소와 가상환경 준비

```bash
git clone https://github.com/VipaForENG/Vipa_backend.git
cd Vipa_backend
python -m venv venv
```

Windows:

```powershell
venv\Scripts\activate
```

macOS / Linux:

```bash
source venv/bin/activate
```

```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정

프로젝트 루트에 `.env`를 작성합니다. 기능별로 DB·AI·메일·소셜 로그인·Storage 설정이 필요합니다.

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE
SECRET_KEY=YOUR_SECRET_KEY
ALGORITHM=HS256

OPENAI_API_KEY=YOUR_OPENAI_API_KEY
OPENAI_MODEL=gpt-4o-mini
GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID

MAIL_USERNAME=YOUR_EMAIL
MAIL_PASSWORD=YOUR_APP_PASSWORD
MAIL_FROM=YOUR_EMAIL
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com

SUPABASE_URL=YOUR_SUPABASE_URL
SUPABASE_SERVICE_KEY=YOUR_SUPABASE_SERVICE_KEY
SUPABASE_BUCKET_NAME=profiles
SUPABASE_AUDIO_BUCKET_NAME=audio
```

키와 비밀번호는 실제 환경의 값으로 설정하고 Git에 올리지 않습니다.

### 3. DB 준비와 서버 실행

PostgreSQL에 사용할 DB를 생성하고 `DATABASE_URL`에 연결 정보를 설정합니다.

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

- Swagger: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- API 기본 경로: `/api/v1`

Android 에뮬레이터에서 로컬 서버에 연결할 때는 일반적으로 `http://10.0.2.2:8000/api/v1`을 사용합니다.

SQLite 로컬 모드는 `VIPA_USE_SQLITE=true`로 설정할 수 있습니다. PostgreSQL을 사용하는 팀 개발 환경과 구분해 사용합니다.

</details>
