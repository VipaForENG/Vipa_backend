from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RobotStatus(BaseModel):
    energy_level: int
    robot_ip: Optional[str] = None
    is_auto_connect: bool
    motor_pitch_angle: int
    motor_yaw_angle: int
    last_sync_at: Optional[datetime] = None

    class Config:
        from_attributes = True