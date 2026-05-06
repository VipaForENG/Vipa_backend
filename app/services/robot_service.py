# [모듈 설명] 로봇의 상태를 데이터베이스에 반영하고 비즈니스 로직을 처리하는 서비스 계층
import asyncio
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any

from app.models.robot import RobotControl

async def connect_to_robot(db: Session, user_id: int, ip: str) -> RobotControl:
    """
    [함수 역할] IP를 입력받아 해당 유저의 로봇 연결 정보를 DB에 저장하거나 갱신합니다.
    [로직 흐름] 유저의 로봇 정보 조회 -> 없으면 INSERT, 있으면 UPDATE -> Commit 후 갱신된 객체 반환
    """
    # [변수 사용] db_robot: DB에서 조회된 로봇 제어 레코드
    db_robot = db.query(RobotControl).filter(RobotControl.user_id == user_id).first()
    
    if not db_robot:
        db_robot = RobotControl(user_id=user_id, robot_ip=ip, last_sync_at=datetime.utcnow())
        db.add(db_robot)
    else:
        db_robot.robot_ip = ip
        db_robot.last_sync_at = datetime.utcnow()
        
    db.commit()
    db.refresh(db_robot)
    
    return db_robot

async def get_current_status(db: Session, user_id: int) -> RobotControl | None:
    """
    [함수 역할] 특정 유저의 현재 로봇 상태를 DB에서 불러옵니다.
    """
    return db.query(RobotControl).filter(RobotControl.user_id == user_id).first()

async def update_face_display(face: str) -> Dict[str, Any]:
    """
    [함수 역할] 디스플레이 표정 변경 (DB 저장 불필요, 통신만 시뮬레이션)
    """
    print(f"[Hardware Command] 표정 전송 시작: {face}")
    await asyncio.sleep(1.0) 
    print(f"[Hardware Command] 표정 전송 완료: {face}")
    return {"success": True, "message": f"Face updated to {face}"}

async def adjust_motor_angle(db: Session, user_id: int, axis: str, direction: str) -> RobotControl:
    """
    [함수 역할] 모터 조작 명령을 받아 각도를 계산하고 DB에 반영합니다.
    [로직 흐름] '위아래'는 pitch 연산, '좌우'는 yaw 연산으로 분기 처리 -> DB 동기화 시간 갱신 -> Commit
    """
    db_robot = db.query(RobotControl).filter(RobotControl.user_id == user_id).first()
    if not db_robot:
        raise ValueError("로봇이 연결되지 않았습니다. 먼저 연결을 진행해주세요.")

    # [변수 사용] step: 버튼 1회 클릭 시 조절할 각도 단위
    step = 5 
    
    if axis == "위아래":
        if direction == "올리기":
            db_robot.motor_pitch_angle += step
        elif direction == "내리기":
            db_robot.motor_pitch_angle -= step
        else:
            raise ValueError("올바르지 않은 방향입니다.")
            
    elif axis == "좌우":
        if direction == "올리기": 
            db_robot.motor_yaw_angle += step
        elif direction == "내리기": 
            db_robot.motor_yaw_angle -= step
        else:
            raise ValueError("올바르지 않은 방향입니다.")
    else:
        raise ValueError("올바르지 않은 축입니다. '위아래' 또는 '좌우'를 입력하세요.")

    db_robot.last_sync_at = datetime.utcnow()
    db.commit()
    db.refresh(db_robot)
    
    return db_robot

async def execute_sound_test() -> Dict[str, Any]:
    """
    [함수 역할] 스피커 사운드 테스트 실행 (DB 저장 불필요)
    """
    print("[Hardware Command] 사운드 테스트 재생 중...")
    await asyncio.sleep(1.0)
    return {"success": True, "message": "Sound test initiated"}