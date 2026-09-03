# 🇺🇸 VIPA Backend

<div align="center">

### CEFR-based AI English Learning Platform Backend

**사용자의 영어 수준을 분석하고,
레벨에 맞는 AI 회화 · 실전 시나리오 · 어휘 학습을 제공하는 영어 학습 플랫폼의 Backend Server입니다.**

<br>

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge\&logo=python\&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge\&logo=fastapi\&logoColor=white)

`REST API` `Pydantic` `Uvicorn`

<br>

## Database

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge\&logo=postgresql\&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge\&logo=sqlalchemy\&logoColor=white)

`SQLAlchemy` `AsyncSession` `asyncpg` `Alembic`

<br>

## Authentication

`JWT` `OAuth 2.0` `bcrypt`

![Google](https://img.shields.io/badge/Google%20Login-4285F4?style=for-the-badge\&logo=google\&logoColor=white)
![Kakao](https://img.shields.io/badge/Kakao%20Login-FFCD00?style=for-the-badge\&logo=kakao\&logoColor=000000)

<br>

## AI

![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge\&logo=openai\&logoColor=white)

`AsyncOpenAI`
`Structured JSON Output`
`CEFR Evaluation`
`Conversation Generation`
`Generative Evaluation`

<br>

## Storage

![Supabase](https://img.shields.io/badge/Supabase%20Storage-3FCF8E?style=for-the-badge\&logo=supabase\&logoColor=white)

`Profile Images` `Conversation Audio`

<br>

</div>

<br>

---

# 📌 Project Overview

**VIPA**는 사용자의 영어 실력을 CEFR 기준으로 분석하고,
분석된 수준에 맞는 영어 학습 콘텐츠를 제공하는 AI 영어 학습 애플리케이션입니다.

이 저장소는 VIPA 서비스의 **Backend Server**이며,

```text
User
  ↓
Authentication
  ↓
CEFR Level Test
  ↓
User Level
  ↓
┌────────────────────────────┐
│                            │
▼                            ▼
AI Conversation        Scenario Learning
│                            │
▼                            ▼
Study Log            Correction / Feedback
│                            │
└──────────────┬─────────────┘
               ↓
      Vocabulary Learning
               ↓
       Learning History
               ↓
          Home Summary
```

와 같이 사용자의 영어 수준을 중심으로 여러 학습 기능이 연결되도록 설계했습니다.

<br>

---

# 👨‍💻 엄인섭 — Backend Lead

팀 프로젝트에서 Backend 파트를 담당하며
서비스의 데이터 구조와 API 흐름을 중심으로 개발했습니다.

### 주요 담당 영역

* Backend 전체 구조 설계
* ERD 및 Database Modeling
* FastAPI REST API 설계
* PostgreSQL 데이터 구조 설계
* 사용자 / 인증 API
* JWT Authentication
* CEFR Level Test 구조
* AI Conversation API
* Scenario Learning 구조
* Vocabulary Learning 구조
* 학습 History 및 Dashboard API
* OpenAI API Integration
* Flutter Client ↔ Backend API 연동
* 팀 내 Backend 기능 통합 및 데이터 흐름 관리

<br>

---

# 🧠 Core Concept

VIPA의 핵심은 모든 사용자에게 동일한 영어 콘텐츠를 제공하는 것이 아니라,

> **사용자의 CEFR Level을 기준으로 학습 난이도와 AI 응답을 개인화하는 것**

입니다.

```text
Level Test
    ↓
CEFR Level
    ↓
┌──────────────────────────┐
│ A1 / A2 / B1 / B2 / C1  │
│            / C2          │
└────────────┬─────────────┘
             ↓
 Personalized Learning
             ↓
 ┌───────────┼───────────┐
 ▼           ▼           ▼
Conversation Scenario Vocabulary
```

사용자의 Level 정보는 단순 화면 표시용 데이터가 아니라
Conversation, Scenario, Vocabulary 모듈에서 실제 학습 난이도를 결정하는 기준으로 사용됩니다.

<br>

---

# 🏗️ System Architecture

```text
┌─────────────────────────────────────┐
│            Flutter Client           │
└─────────────────┬───────────────────┘
                  │
                  │ REST API / JWT
                  ▼
┌─────────────────────────────────────┐
│            FastAPI Backend          │
│                                     │
│ Auth       Level       User         │
│ Chat       Scenario    Vocabulary   │
│ History    Category    Home         │
└───────┬──────────────┬──────────────┘
        │              │
        │              │
        ▼              ▼
┌──────────────┐  ┌─────────────────┐
│ PostgreSQL   │  │   OpenAI API    │
│              │  │                 │
│ User         │  │ Level Test      │
│ Level        │  │ Conversation    │
│ Scenario     │  │ Evaluation      │
│ Study Log    │  │ Scenario Gen.   │
│ Vocabulary   │  │ Hints           │
└──────┬───────┘  └─────────────────┘
       │
       ▼
┌─────────────────┐
│ Supabase Storage│
│                 │
│ Profile Image   │
│ Audio File      │
└─────────────────┘
```

<br>

---

# 🔐 Authentication

VIPA는 일반 회원가입뿐 아니라
Google / Kakao Social Login도 지원합니다.

## Email Authentication

```text
Sign Up
   ↓
Password Hashing
   ↓
PostgreSQL
   ↓
Login
   ↓
JWT Access Token
```

### Features

* 이메일 회원가입
* 이메일 / 비밀번호 로그인
* bcrypt 기반 Password Hashing
* JWT Access Token 발급
* Bearer Token 기반 API 인증
* 사용자 정보 조회
* 비밀번호 변경
* 회원 탈퇴

<br>

## Social Login

### Google

```text
Google Access Token
        ↓
Google UserInfo
        ↓
Email / Nickname
        ↓
Find or Create User
        ↓
VIPA JWT
```

### Kakao

```text
Kakao Access Token
        ↓
Kakao UserInfo
        ↓
Email / Nickname
        ↓
Find or Create User
        ↓
VIPA JWT
```

동일한 이메일을 기준으로 Social Provider 정보를 통합할 수 있도록 구성했습니다.

<br>

---

# 📧 Password Recovery

이메일 인증 코드를 이용한 비밀번호 재설정 기능을 구현했습니다.

```text
Email
  ↓
User Validation
  ↓
6-Digit Code
  ↓
Email Delivery
  ↓
10 Minute Expiration
  ↓
Code Verification
  ↓
New Password
```

### Flow

```text
POST
/password-recovery/send-code

        ↓

POST
/password-recovery/verify-code

        ↓

PATCH
/password-recovery/reset
```

인증 코드는 Database에 만료시간과 함께 저장되고
사용 완료 후 제거됩니다.

<br>

---

# 👤 User Profile

사용자의 기본 프로필을 Backend에서 관리합니다.

### Features

* 내 정보 조회
* 닉네임 수정
* 프로필 이미지 수정
* 닉네임 중복 확인
* 비밀번호 변경
* 회원 탈퇴

프로필 이미지는 서버 로컬 파일 시스템이 아니라
**Supabase Storage**에 저장합니다.

```text
Flutter
   ↓
UploadFile
   ↓
FastAPI
   ↓
UUID File Name
   ↓
Supabase Storage
   ↓
Public URL
   ↓
PostgreSQL
```

<br>

---

# 📊 CEFR Level Test

VIPA의 개인화 학습을 시작하는 핵심 기능입니다.

CEFR:

```text
A1
A2
B1
B2
C1
C2
```

를 기준으로 사용자의 영어 수준을 분석합니다.

<br>

## 1. Question Generation

OpenAI API를 이용하여
여러 CEFR 난이도가 혼합된 **20개의 Level Test 문제**를 생성합니다.

```text
Level Test Start
       ↓
OpenAI
       ↓
20 Questions
       ↓
A1 ~ C2 Mixed Difficulty
```

각 문제에는

```text
ID
CEFR Level
Question
Options
Answer
Korean Translation
```

데이터가 포함됩니다.

<br>

## 2. User Answer Analysis

사용자가 20문제를 제출하면
AI가 답변 전체를 분석합니다.

```text
20 User Answers
       ↓
OpenAI Analysis
       ↓
CEFR Level
Overall Score
Grammar Score
Vocabulary Score
Weakness Tags
Detailed Feedback
```

<br>

## 3. Level Storage

최종 결과는 두 종류의 데이터로 분리합니다.

```text
UserLevel
│
├── Current CEFR Level
└── Overall Score

LevelTestResult
│
├── Detailed Analysis
├── Weakness Tags
└── Test History
```

현재 사용자의 Level과
과거 Level Test 분석 History를 분리하여 저장합니다.

<br>

---

# 💬 AI Conversation

사용자의 CEFR Level에 맞춰
AI와 자유 영어 회화를 진행할 수 있습니다.

```text
User
 ↓
JWT
 ↓
Current CEFR Level
 ↓
Conversation Session
 ↓
Recent Messages
 ↓
OpenAI
 ↓
English Response
Korean Translation
Grammar Feedback
Understanding Score
 ↓
Conversation Log
 ↓
Study Log
```

<br>

## Personalized Conversation

AI Prompt에 현재 사용자의 CEFR Level을 전달합니다.

예:

```text
User CEFR Level = B1

       ↓

Vocabulary Complexity = B1
Grammar Complexity = B1
Response Difficulty = B1
```

따라서 A1 사용자와 B2 사용자가
같은 질문을 하더라도 난이도에 맞춘 응답을 받을 수 있도록 구성했습니다.

<br>

## Conversation Context

매 메시지를 독립적으로 처리하지 않고
최근 대화 History를 다음 요청의 Context로 전달합니다.

```text
Recent 5 Messages
       +
Current User Message
       ↓
OpenAI
```

이를 통해 대화의 흐름을 일정 수준 유지합니다.

<br>

## AI Response

```json
{
  "en": "AI English response",
  "ko": "한국어 번역",
  "feedback": "Grammar feedback",
  "understanding_score": 85
}
```

<br>

## Study Data

정상적으로 대화가 완료되면

```text
Conversation Turn
       ↓
Study Log
       ↓
Daily Study Summary
       ↓
Study Count / Energy
```

로 이어지도록 구성했습니다.

<br>

---

# 🎭 AI Scenario Learning

VIPA의 실전 영어 회화 학습 모듈입니다.

공항, 은행, 병원, 회사 등 실제 상황을 기반으로
사용자의 CEFR Level에 맞는 역할극을 생성합니다.

<br>

## Scenario Flow

```text
Category
   ↓
Situation
   ↓
User CEFR Level
   ↓
OpenAI
   ↓
17-Turn Scenario
   ↓
Conversation Session
   ↓
User Response
   ↓
AI Evaluation
   ↓
Correction / Feedback
   ↓
Session Complete
```

<br>

## Default Situations

서버 초기화 시 주요 학습 상황을 Seed Data로 구성합니다.

```text
공항
├── 출입국 심사
└── 수하물 분실

은행
└── 계좌 개설

병원
└── 진료 접수

학교
└── 수강 신청

백화점
└── 환불 요청

회사
└── 프로젝트 회의

마트
└── 물건 찾기

그 외
└── 카페 주문
```

각 Situation에는 AI가 수행할 Role도 함께 저장됩니다.

<br>

---

# 🤖 Scenario Generation

사용자의 CEFR Level과 선택한 상황을 이용하여
**17 Turn 영어 Roleplay Scenario**를 생성합니다.

```text
CEFR Level
    +
Situation
    +
AI Role
    ↓
OpenAI
    ↓
17 Turns
```

구조:

```text
AI
 ↓
User
 ↓
AI
 ↓
User
 ↓
...
 ↓
AI
```

총

```text
9 AI Turns
8 User Turns
```

로 구성됩니다.

<br>

## Scenario Data

사용자 Turn에는

```text
Expected English Answer
Korean Translation
Keywords
```

를 함께 생성합니다.

예:

```json
{
  "speaker": "user",
  "expected_en": "I'd like to open a new account.",
  "ko": "새 계좌를 개설하고 싶습니다.",
  "keywords": [
    "open",
    "account"
  ]
}
```

<br>

---

# ✅ Generative Evaluation

사용자가 반드시 Expected Answer와 동일한 문장을 말해야
정답으로 처리하는 방식은 사용하지 않습니다.

```text
Expected Answer
      +
User Answer
      +
CEFR Level
      ↓
AI Evaluation
```

AI가

* 문맥 적합성
* 문법
* 표현의 자연스러움

을 함께 판단합니다.

### Response

```json
{
  "is_pass": true,
  "feedback_ko": "표현은 자연스럽지만...",
  "corrected_en": "I'd like to open an account."
}
```

교정 결과는 Database에 저장하여
이후 학습 History에서 다시 확인할 수 있도록 구성했습니다.

<br>

---

# 💡 3-Level Hint System

실전 회화에서 사용자가 막혔을 때
3단계 힌트를 제공합니다.

## Level 1

핵심 Keyword 제공

```text
open, account
```

## Level 2

문장의 시작 부분 제공

```text
I'd like ...
```

## Level 3

전체 Expected Answer 제공

```text
I'd like to open a new account.
```

Level 1 / 2는 AI API를 다시 호출하지 않고
이미 생성된 Scenario Data를 이용하여 빠르게 처리합니다.

Level 3에서는 정답 전체가 공개되므로 Penalty Flag를 반환합니다.

<br>

---

# 🎙️ Conversation Audio

Scenario 학습이 끝난 후
사용자의 회화 녹음 파일을 저장할 수 있습니다.

지원 형식:

```text
m4a
wav
mp3
aac
```

### Flow

```text
Flutter Audio
     ↓
FastAPI Upload
     ↓
File Validation
     ↓
Supabase Storage
     ↓
Audio URL
     ↓
ConversationSession
```

<br>

---

# 📝 Conversation History

실전 회화가 끝난 후
과거 학습 Session을 다시 조회할 수 있습니다.

### History

```text
User
 ↓
Conversation Sessions
 ↓
Recent Sessions
```

### Session Detail

```text
ConversationSession
        ↓
ConversationTurn
        ↓
User Input
Correction
Feedback
```

특정 Session을 선택하면
사용자와 AI가 진행했던 대화와 교정 내용을 다시 확인할 수 있습니다.

Flutter에서는 해당 데이터를 이용하여
대화 Script 형태의 History 화면을 구성합니다.

<br>

---

# 📚 Vocabulary Learning

VIPA의 별도 어휘 학습 모듈입니다.

사용자의 CEFR Level과 기존 학습 상태를 기반으로
문제를 분리하여 제공합니다.

```text
User CEFR Level
       +
Vocabulary Study History
       ↓
Personalized Vocabulary Quiz
```

<br>

## Vocabulary Dataset

Vocabulary Master Table은
**AI Hub 기반 영어 학습 데이터를 저장할 수 있도록 설계**했습니다.

```text
Vocabulary
    ↓
User Vocabulary Study
    ↓
Learning Detail
```

Master Vocabulary와 사용자별 학습 상태를 분리하여
여러 사용자가 동일 Vocabulary Data를 공유하면서도
각자의 숙련 상태는 독립적으로 관리하도록 구성했습니다.

<br>

---

# 🧩 Personalized Quiz

문제를 세 가지 유형으로 분리합니다.

```text
New
Review
Retry
```

사용자는 각 유형의 문제 개수를 지정하여
맞춤형 Quiz Session을 구성할 수 있습니다.

기본 설정:

```text
New     = 5
Review  = 10
Retry   = 10
```

<br>

---

# ✅ Real-time Answer Check

각 문제의 답안을 즉시 확인할 수 있습니다.

```text
User Answer
     ↓
Answer Validation
     ↓
Attempt Count
     ↓
Feedback
```

### First Attempt

```text
Wrong
 ↓
Hint
```

### Repeated Attempt

```text
Wrong
 ↓
AI Hint
 ↓
Wrong History Update
```

단순 정답/오답만 반환하지 않고
사용자의 잘못된 단어 선택과 정답 표현의 차이를 설명하는 AI Hint도 제공합니다.

<br>

---

# ⭐ Bookmark

학습 중 다시 보고 싶은 Vocabulary를
즐겨찾기로 관리할 수 있습니다.

### Features

* Bookmark On / Off
* Bookmark List
* 사용자별 Bookmark 상태 관리

<br>

---

# 📈 Vocabulary History

오늘의 학습 결과를 집계합니다.

```text
Today's Quiz
    ↓
Solved Count
Correct Count
Accuracy
    ↓
Wrong Vocabulary
```

### 제공 데이터

* 오늘 푼 문제 수
* 정답 수
* 정답률
* 누적 오답 단어
* 단어별 오답 횟수

<br>

---

# 🏠 Home Dashboard

Flutter Home 화면에서 여러 API를 개별 호출하지 않도록
Backend에서 필요한 학습 정보를 하나의 Summary Response로 구성합니다.

```text
User
 ↓
Home Summary
 ↓
Daily Study Data
Level
Energy
Learning Progress
```

Backend에서 데이터를 집계해 반환하여
Client가 화면 표시 로직에 집중할 수 있도록 구성했습니다.

<br>

---

# 🗄️ Database Design

VIPA는 학습 기능별 데이터를 하나의 Table에 몰아넣지 않고
Domain 단위로 분리했습니다.

### Main Domains

```text
USER
│
├── users
│
├── user_levels
└── level_test_results


CATEGORY
│
├── main_category
└── sub_category


CONVERSATION
│
├── custom_scenario
├── conversation_session
├── conversation_turn
└── sentence_log


LEARNING
│
├── study_log
└── daily_study_summary


VOCABULARY
│
├── vocabulary
├── vocabulary_study
└── vocab_learning_detail
```

<br>

---

# 🔗 Core Data Relationships

```text
User
 │
 ├───────────────┐
 │               │
 ▼               ▼
UserLevel     StudyLog
 │
 ▼
LevelTestResult


User
 │
 ▼
CustomScenario
 │
 ▼
ConversationSession
 │
 ├──────────────┐
 ▼              ▼
ConversationTurn
             SentenceLog


User
 │
 ▼
VocabularyStudy
 │
 ▼
Vocabulary


User
 │
 ▼
VocabLearningDetail
```

<br>

---

# 🧱 Backend Architecture

프로젝트 구조는 역할별로 분리했습니다.

```text
Client
   ↓
Route
   ↓
Service / CRUD
   ↓
SQLAlchemy
   ↓
Database
```

AI 기능이 필요한 경우:

```text
Route
   ↓
Service
   ├───────────▶ OpenAI
   │
   ▼
CRUD
   ↓
Database
```

<br>

---

# 📂 Project Structure

```text
Vipa_backend/
│
├── app/
│   │
│   ├── api/
│   │   ├── deps.py
│   │   └── v1/
│   │       └── auth.py
│   │
│   ├── core/
│   │   ├── ai_client.py
│   │   ├── base_data.py
│   │   ├── config.py
│   │   ├── constants.py
│   │   ├── database.py
│   │   ├── mail.py
│   │   ├── security.py
│   │   └── storage.py
│   │
│   ├── crud/
│   │   ├── chat.py
│   │   ├── conversation.py
│   │   ├── daily_summary.py
│   │   ├── level.py
│   │   ├── user.py
│   │   └── vocabulary.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── level.py
│   │   ├── category.py
│   │   ├── custom_scenario.py
│   │   ├── conversation_session.py
│   │   ├── conversation_turn.py
│   │   ├── sentence_log.py
│   │   ├── study_log.py
│   │   ├── summary.py
│   │   ├── vocabulary.py
│   │   ├── vocabulary_study.py
│   │   └── vocab_learning_detail.py
│   │
│   ├── routes/
│   │   ├── user.py
│   │   ├── level.py
│   │   ├── home.py
│   │   ├── chat.py
│   │   ├── category.py
│   │   ├── scenario.py
│   │   ├── conversation.py
│   │   └── vocabulary.py
│   │
│   ├── schemas/
│   │
│   ├── services/
│   │   ├── scenario_service.py
│   │   └── audio_service.py
│   │
│   ├── utils/
│   │   └── gpt5.py
│   │
│   └── main.py
│
├── alembic/
├── alembic.ini
├── requirements.txt
└── README.md
```

<br>

---

# ⚡ Sync / Async Database Flow

VIPA에서는 일반 CRUD와 AI Conversation 처리의 특성에 따라
SQLAlchemy의 Sync / Async Session을 함께 사용합니다.

### Sync

```text
Session
 ↓
User
Level
Scenario
Vocabulary
History
```

### Async

```text
AsyncSession
 ↓
AI Conversation
Daily Summary
```

PostgreSQL 비동기 연결에는

```text
asyncpg
```

를 사용합니다.

<br>

---

# 📡 Main API Domains

Base URL:

```text
/api/v1
```

<br>

## User

```text
/users
```

* 회원가입
* 로그인
* 내 정보 조회
* 비밀번호 복구
* 비밀번호 변경
* 프로필 수정
* 회원탈퇴

<br>

## Social Authentication

```text
/auth
```

* Google Login
* Kakao Login

<br>

## Level Test

```text
/level-test
```

* Level Test 문제 생성
* 사용자 답변 평가
* CEFR Level 저장

<br>

## Conversation

```text
/chat
```

* AI 자유 영어 회화
* Conversation Session
* Grammar Feedback

<br>

## Scenario

```text
/scenario
```

* 실전 Scenario 생성
* 사용자 발화 평가
* 단계별 Hint
* Session 완료
* Audio Upload

<br>

## Category

```text
/category
```

* Main Category 조회
* Sub Category 조회

<br>

## Vocabulary

```text
/vocabulary
```

* Vocabulary Dashboard
* 맞춤 Quiz
* 실시간 답안 검사
* Quiz 결과 저장
* Bookmark
* Daily History
* Wrong Note

<br>

## Conversation History

```text
/conversation
```

* Session History
* Conversation Script
* Correction History

<br>

## Home

```text
/home
```

* Home Summary

<br>

---

# 🔐 Environment Variables

프로젝트 Root에 `.env` 파일을 생성합니다.

```env
DATABASE_URL=

SECRET_KEY=
ALGORITHM=HS256

OPENAI_API_KEY=
OPENAI_MODEL=

GOOGLE_CLIENT_ID=

MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com

SUPABASE_URL=
SUPABASE_SERVICE_KEY=
SUPABASE_BUCKET_NAME=profiles
SUPABASE_AUDIO_BUCKET_NAME=audio
```

> Secret Key와 API Key는 Repository에 Commit하지 않습니다.

<br>

---

# 💾 Database Environment

PostgreSQL을 기본 Database로 사용합니다.

```text
DATABASE_URL
    ↓
PostgreSQL
```

개발 환경에서 Database URL이 설정되지 않았거나
연결이 불가능한 경우 SQLite를 Fallback으로 사용할 수 있도록 구성했습니다.

```text
PostgreSQL
   │
   └── Connection Failure
            ↓
         SQLite
```

강제로 Local SQLite를 사용하려면:

```env
VIPA_USE_SQLITE=true
```

<br>

---

# 🚀 Getting Started

## 1. Clone Repository

```bash
git clone https://github.com/VipaForENG/Vipa_backend.git
cd Vipa_backend
```

<br>

## 2. Create Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

<br>

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

<br>

## 4. Environment Configuration

`.env` 파일을 작성합니다.

```env
DATABASE_URL=YOUR_POSTGRESQL_URL
SECRET_KEY=YOUR_SECRET_KEY

OPENAI_API_KEY=YOUR_OPENAI_API_KEY
OPENAI_MODEL=gpt-4o-mini

MAIL_USERNAME=YOUR_EMAIL
MAIL_PASSWORD=YOUR_MAIL_PASSWORD
MAIL_FROM=YOUR_EMAIL

SUPABASE_URL=YOUR_SUPABASE_URL
SUPABASE_SERVICE_KEY=YOUR_SUPABASE_SERVICE_KEY
```

<br>

## 5. Database Migration

```bash
alembic upgrade head
```

<br>

## 6. Run Server

```bash
uvicorn app.main:app --reload
```

<br>

## 7. Swagger

```text
http://127.0.0.1:8000/docs
```

OpenAPI:

```text
/api/v1/openapi.json
```

<br>

---

# 🔄 Overall Data Flow

```text
Flutter
   ↓
FastAPI
   ↓
JWT Authentication
   ↓
User
   ↓
CEFR Level
   ↓
┌─────────────┬──────────────┬──────────────┐
│             │              │              │
▼             ▼              ▼              ▼
Chat       Scenario      Vocabulary       Home
│             │              │              │
│          OpenAI            │              │
│             │              │              │
└─────────────┴──────┬───────┴──────────────┘
                     ↓
                 Study Data
                     ↓
                 PostgreSQL
                     ↓
             History / Summary
                     ↓
                  Flutter
```

<br>

---

# 💡 Key Design Points

## 1. CEFR Level을 중심으로 기능 연결

Level Test 결과를 단순히 보여주고 끝내지 않고

```text
CEFR
 ↓
Conversation
Scenario
Vocabulary
```

의 난이도 결정에 다시 사용합니다.

<br>

## 2. AI Output을 구조화된 데이터로 처리

AI가 자유 형식 Text만 반환하도록 두지 않고
JSON Schema 기반 응답을 요구합니다.

예:

```json
{
  "cefr_level": "B1",
  "overall_score": 75.5,
  "weakness_tags": "시제오류, 어휘부족"
}
```

또는:

```json
{
  "is_pass": true,
  "feedback_ko": "...",
  "corrected_en": "..."
}
```

Backend에서 파싱하고 Database에 저장할 수 있는
구조화된 결과로 처리합니다.

<br>

## 3. 학습 결과를 History로 축적

```text
AI Response
     ↓
Database
     ↓
Learning History
```

형태로 설계하여 AI 응답이 일회성 결과로 끝나지 않도록 했습니다.

<br>

## 4. 학습 Domain별 데이터 분리

```text
Account
Level
Conversation
Vocabulary
Study Log
```

를 분리하여 각 기능이 자신의 역할을 갖도록 설계했습니다.

<br>

## 5. Client와 Backend 역할 분리

Flutter에서는

```text
UI
State
User Interaction
```

에 집중하고,

Backend에서는

```text
Authentication
Business Logic
Database
AI
Learning Data
```

를 담당하도록 역할을 나눴습니다.

<br>

---

# 🎯 What I Learned

VIPA Backend를 개발하면서
단순 CRUD API를 넘어 **여러 기능이 하나의 데이터 흐름으로 연결되는 Backend Service**를 설계하고 구현했습니다.

### Backend

* FastAPI REST API
* Router 분리
* Pydantic Schema
* Business Logic / CRUD 분리
* Sync / Async API 처리
* Exception Handling

### Database

* PostgreSQL
* SQLAlchemy
* AsyncSession
* 관계형 Data Modeling
* ERD
* Foreign Key
* Cascade
* Alembic Migration

### Authentication

* JWT
* bcrypt Password Hashing
* Google Social Login
* Kakao Social Login
* Email Verification
* Protected API

### AI

* OpenAI API Integration
* Async LLM Request
* Structured JSON Output
* CEFR Level Analysis
* Level-aware AI Conversation
* Dynamic Scenario Generation
* Generative Answer Evaluation
* AI Hint Generation

### Learning System

* CEFR Level
* Conversation Session
* Learning History
* Study Log
* Daily Summary
* Personalized Vocabulary
* Wrong Answer History

### Storage

* Supabase Storage
* User Profile Image
* Conversation Audio

### Integration

* Flutter ↔ FastAPI
* REST API
* JWT Bearer Authentication
* JSON-based Data Flow

<br>

---

# 📈 Project Summary

| Item              | Description                                  |
| ----------------- | -------------------------------------------- |
| Project           | VIPA                                         |
| Type              | Team Project                                 |
| Role              | Backend Lead                                 |
| Backend           | FastAPI                                      |
| Language          | Python                                       |
| Main Database     | PostgreSQL                                   |
| ORM               | SQLAlchemy                                   |
| Migration         | Alembic                                      |
| AI                | OpenAI API                                   |
| Authentication    | JWT / Google / Kakao                         |
| Storage           | Supabase Storage                             |
| Client            | Flutter                                      |
| Learning Standard | CEFR A1 ~ C2                                 |
| Main Modules      | Level / Conversation / Scenario / Vocabulary |
| API Style         | REST API                                     |

<br>

---

# 📱 Frontend Repository

### VIPA Frontend

https://github.com/VipaForENG/Vipa_frontend

<br>

---

# 🚀 Getting Started

## 1. Clone Repository

```bash
git clone https://github.com/VipaForENG/Vipa_backend.git
cd Vipa_backend
```

<br>

## 2. Create Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

<br>

## 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

주요 Backend Dependency:

```text
FastAPI
Uvicorn

SQLAlchemy
PostgreSQL
asyncpg
Alembic

JWT
bcrypt

OpenAI API
Supabase

FastAPI Mail
```

<br>

## 4. Configure Environment Variables

프로젝트 Root에 `.env` 파일을 생성합니다.

```env
# Database
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE

# JWT
SECRET_KEY=YOUR_SECRET_KEY
ALGORITHM=HS256

# OpenAI
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
OPENAI_MODEL=gpt-4o-mini

# Mail
MAIL_USERNAME=YOUR_EMAIL
MAIL_PASSWORD=YOUR_APP_PASSWORD
MAIL_FROM=YOUR_EMAIL
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com

# Supabase
SUPABASE_URL=YOUR_SUPABASE_URL
SUPABASE_SERVICE_KEY=YOUR_SUPABASE_SERVICE_KEY
SUPABASE_BUCKET_NAME=profiles
SUPABASE_AUDIO_BUCKET_NAME=audio
```

> API Key, Database Password, JWT Secret과 같은 민감한 값은 Repository에 Commit하지 않습니다.

<br>

## 5. Prepare PostgreSQL

PostgreSQL에 VIPA에서 사용할 Database를 생성합니다.

예:

```sql
CREATE DATABASE vipa;
```

이후 `.env`의 `DATABASE_URL`을 생성한 Database에 맞게 설정합니다.

예:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/vipa
```

<br>

## 6. Run Database Migration

VIPA는 **Alembic**을 이용해 Database Schema Migration을 관리합니다.

```bash
alembic upgrade head
```

Migration 상태 확인:

```bash
alembic current
```

Migration History 확인:

```bash
alembic history
```

<br>

## 7. Run Backend Server

개발 서버를 실행합니다.

```bash
uvicorn app.main:app --reload
```

기본 서버 주소:

```text
http://127.0.0.1:8000
```

<br>

## 8. API Documentation

FastAPI에서 자동 생성되는 API 문서를 확인할 수 있습니다.

### Swagger UI

```text
http://127.0.0.1:8000/docs
```

### ReDoc

```text
http://127.0.0.1:8000/redoc
```

<br>

## 9. API Base URL

VIPA Backend의 주요 API는 다음 Prefix를 사용합니다.

```text
/api/v1
```

예:

```text
http://127.0.0.1:8000/api/v1/users
http://127.0.0.1:8000/api/v1/auth
http://127.0.0.1:8000/api/v1/level-test
http://127.0.0.1:8000/api/v1/chat
http://127.0.0.1:8000/api/v1/scenario
http://127.0.0.1:8000/api/v1/vocabulary
```

<br>

---

# 💻 Local Development

전체 개발 환경의 기본 흐름은 다음과 같습니다.

```text
Clone Repository
       ↓
Virtual Environment
       ↓
Install Dependencies
       ↓
.env
       ↓
PostgreSQL
       ↓
Alembic Migration
       ↓
FastAPI
       ↓
Swagger
       ↓
Flutter Client
```

Frontend와 함께 실행할 경우:

```text
Flutter
   ↓
http://127.0.0.1:8000/api/v1
   ↓
FastAPI
   ↓
PostgreSQL
```

Android Emulator에서 Local Backend에 접근하는 경우
Frontend에서는 일반적으로 다음 주소를 사용합니다.

```text
http://10.0.2.2:8000/api/v1
```

<br>

---

# 🧪 Optional — SQLite Local Mode

VIPA Backend에는 PostgreSQL 연결 정보가 없는 경우
Local SQLite를 사용하는 Fallback 구조가 포함되어 있습니다.

강제로 SQLite를 사용하려면:

### Windows PowerShell

```powershell
$env:VIPA_USE_SQLITE="true"
uvicorn app.main:app --reload
```

### macOS / Linux

```bash
export VIPA_USE_SQLITE=true
uvicorn app.main:app --reload
```

SQLite Database:

```text
vipa_local.db
```

> 실제 서비스 및 팀 개발 환경에서는 PostgreSQL 사용을 권장합니다.

---

# 👨‍💻 Backend Lead

**엄인섭**

GitHub
https://github.com/EddieEom
