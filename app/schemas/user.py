from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# 1. 회원가입 시 앱에서 서버로 보내는 데이터
class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="유저 이메일", json_schema_extra={"example": "user@gmail.com"})
    password: str = Field(..., min_length=6, description="비밀번호", json_schema_extra={"example": "userpassword"})
    nickname: str = Field(..., description="닉네임", json_schema_extra={"example": "VipaUser"})
    
    is_social: int = 0
    social_role: int = 0

# 2. 로그인 시 앱에서 서버로 보내는 데이터
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# 3. 서버가 앱으로 유저 정보를 돌려줄 때
class UserResponse(BaseModel):
    user_id: int
    email: EmailStr
    nickname: Optional[str] = None
    study_count: int
    
    class Config:
        from_attributes = True

# 4. 토큰 응답 (로그인 성공 시 반환)
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    is_tested: bool

# 5. 토큰 해독 시 사용할 데이터 모델
class TokenPayload(BaseModel):
    sub: Optional[int] = None  # 토큰의 'sub' 필드에 담긴 user_id를 추출할 때 사용

# 6. 소셜 로그인 요청 모델 (액세스 토큰을 담아서 보냄)
class SocialLoginRequest(BaseModel):
    access_token: str = Field(..., description="구글/카카오에서 발급받은 액세스 토큰")

# 비밀번호 찾기 이메일 입력용
class PasswordRecoveryEmail(BaseModel):
    email: EmailStr

# 인증 코드 검증용
class VerifyRecoveryCode(BaseModel):
    email: EmailStr
    code: str

# 실제 비밀번호 변경용
class ResetPassword(BaseModel):
    email: EmailStr
    code: str
    new_password: str

# 결과 메시지 응답용
class Msg(BaseModel):
    message: str