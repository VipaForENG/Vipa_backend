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
        # Pydantic V2에서는 from_attributes = True를 사용합니다.
        from_attributes = True

# 4. 토큰 응답
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"