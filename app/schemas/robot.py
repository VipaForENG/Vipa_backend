# [모듈 설명] 로봇 제어 API의 입출력 데이터 규격(Schema)을 정의합니다.
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# (기존 작성하신 응답용 스키마)
class RobotStatus(BaseModel):
    energy_level: int
    robot_ip: Optional[str] = None
    is_auto_connect: bool
    motor_pitch_angle: int
    motor_yaw_angle: int
    last_sync_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# --- 이하 API 요청(Request)을 위한 스키마 추가 ---

class ConnectRequest(BaseModel):
    # [변수 사용] ip: 로봇과 연결할 네트워크 주소
    ip: str

class FaceRequest(BaseModel):
    # [변수 사용] face: 화면에 띄울 표정 텍스트
    face: str

class MotorRequest(BaseModel):
    # [변수 사용] axis: "위아래" (pitch) 또는 "좌우" (yaw)
    axis: str
    # [변수 사용] direction: "올리기" (증가) 또는 "내리기" (감소)
    direction: str