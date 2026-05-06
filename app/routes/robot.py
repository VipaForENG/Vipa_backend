# [모듈 설명] 프론트엔드의 HTTP 요청을 수신하고, JWT 인증을 거친 뒤 DB 세션과 함께 서비스로 전달하는 라우터
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# 스키마, 로직, DB 세션, 유저 모델, 그리고 작성하신 인증 의존성 함수 임포트
from app.schemas.robot import RobotStatus, ConnectRequest, FaceRequest, MotorRequest
from app.services import robot_service
from app.core.database import get_db
from app.models.user import User
from app.api.deps import get_current_active_user # JWT 토큰 검증 후 유저 객체를 반환하는 의존성 함수

router = APIRouter()


@router.post("/connect", response_model=RobotStatus)
async def connect_robot(
    request: ConnectRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user) # JWT 토큰 검증 후 유저 객체 주입
):
    """
    [함수 역할] 로그인한 유저의 식별자(user_id)를 추출하여 해당 유저의 로봇 IP 정보를 DB에 갱신합니다.
    """
    return await robot_service.connect_to_robot(db, current_user.user_id, request.ip)

@router.get("/status", response_model=RobotStatus)
async def get_robot_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    [함수 역할] 현재 로그인한 유저가 소유한 로봇의 상세 상태(에너지, 각도 등) 반환
    """
    robot = await robot_service.get_current_status(db, current_user.user_id)
    if not robot:
        raise HTTPException(status_code=404, detail="등록된 로봇을 찾을 수 없습니다. 먼저 로봇 연결을 진행해주세요.")
    return robot

@router.post("/face")
async def set_robot_face(
    request: FaceRequest,
    current_user: User = Depends(get_current_active_user) # 하드웨어 제어 시에도 보안 적용
):
    """
    [함수 역할] 디스플레이 표정 전송 명령 처리 (로그인 필요)
    """
    # 필요하다면 여기서 current_user.user_id를 활용해 이 유저가 로봇을 가졌는지 검증하는 로직을 추가할 수 있습니다.
    return await robot_service.update_face_display(request.face)

@router.post("/motor", response_model=RobotStatus)
async def adjust_motor(
    request: MotorRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    [함수 역할] 로그인한 유저의 모터 조작 명령을 DB에 반영하고 최신 상태를 반환
    """
    try:
        return await robot_service.adjust_motor_angle(db, current_user.user_id, request.axis, request.direction)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/sound")
async def test_sound(
    current_user: User = Depends(get_current_active_user) # 보안 적용
):
    """
    [함수 역할] 사운드 테스트 실행 (로그인 필요)
    """
    return await robot_service.execute_sound_test()