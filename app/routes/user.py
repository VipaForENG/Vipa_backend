
import os
import uuid
import shutil
from datetime import datetime, timedelta, timezone
import secrets
from typing import cast, Any

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from fastapi_mail import MessageSchema, MessageType

from app.core.database import get_db
from app.core import security
from app.core.mail import fastmail
from app.crud import user as user_crud
from app.schemas.user import (
    Msg, VerifyRecoveryCode, PasswordRecoveryEmail, 
    UserCreate, UserLogin, UserResponse, Token, ResetPassword, PasswordChangeRequest
)
from app.crud import level as level_crud
from app.core.security import get_current_user_id
router = APIRouter()
from app.core.storage import SupabaseStorageService 
from app.models.user import User




# --- [?좎? 湲곕낯 湲곕뒫] ---

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

@router.get("/me", response_model=UserResponse)
def read_user_me(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id) # ?뵍 ?좏겙 寃利??꾨즺
):
    """
    ???뺣낫 議고쉶 API:
    JWT ?좏겙???듯빐 ?몄쬆???좎????곸꽭 ?뺣낫瑜?諛섑솚?⑸땲??
    """
    # 1. DB?먯꽌 ?좎? 議고쉶
    user = user_crud.get_user_by_id(db, user_id=user_id)
    
    # 2. ?좎?媛 ?녿뒗 寃쎌슦(DB ??젣 ??
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="?ъ슜?먮? 李얠쓣 ???놁뒿?덈떎."
        )
    
    # 3. ?좎? ?뺣낫 諛섑솚 (UserResponse ?ㅽ궎留덉뿉 ?곕씪 ?꾩슂???꾨뱶?ㅼ씠 ?섍컩?덈떎)
    return user

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    ?뚯썝媛??API: ?대찓?쇨낵 ?됰꽕?꾩쓣 媛곴컖 寃利앺븯???뺥솗???먮윭 硫붿떆吏瑜??쒓났?⑸땲??
    """
    # 1. ?대찓??以묐났 ?좎젣 ?뺤씤
    if user_crud.get_user_by_email(db, email=user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="?대? ?ъ슜 以묒씤 ?대찓?쇱엯?덈떎."
        )
    
    # 2. ?됰꽕??以묐났 ?좎젣 ?뺤씤 (?댁젣 Pylance ?먮윭媛 ?щ씪吏묐땲??
    if user_crud.get_user_by_nickname(db, nickname=user_in.nickname):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="?대? ?ъ슜 以묒씤 ?됰꽕?꾩엯?덈떎."
        )
    
    # 3. ?곗씠?곕쿋?댁뒪 ???諛??덉쇅 泥섎━
    try:
        new_user = user_crud.create_user(db=db, user_in=user_in)
        return new_user
    except IntegrityError:
        db.rollback()
        # ?좎젣 寃?щ? ?덉쓬?먮룄 ?숈떆???댁뒋濡??먮윭媛 ??寃쎌슦瑜??鍮꾪븳 理쒗썑??諛⑹뼱??
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="?대? ?깅줉???대찓???먮뒗 ?됰꽕?꾩엯?덈떎."
        )

@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    """
    濡쒓렇??API: ?대찓??鍮꾨?踰덊샇 寃利???JWT ?≪꽭???좏겙??諛쒓툒?⑸땲??
    """
    db_user = user_crud.get_user_by_email(db, email=user_in.email)
    
    # DB????λ맂 hashed_password? ?낅젰??plain_password 鍮꾧탳
    # Pylance ????먮윭 諛⑹?瑜??꾪빐 cast(str, ...) ?ъ슜
    if not db_user or not security.verify_password(user_in.password, cast(str, db_user.password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="?대찓???먮뒗 鍮꾨?踰덊샇媛 ?쇱튂?섏? ?딆뒿?덈떎."
        )

    # ?덈꺼 ?뚯뒪??湲곕줉???덈뒗吏 ?뺤씤
    # level_crud???좎????덈꺼 ?뺣낫瑜?媛?몄삤???⑥닔媛 ?덈떎怨?媛?뺥빀?덈떎.
    user_level = level_crud.get_user_level(db, user_id=db_user.user_id)
    is_tested = True if user_level else False


    # ?좎? ID瑜?湲곕컲?쇰줈 ?≪꽭???좏겙 ?앹꽦
    access_token = security.create_access_token(subject=db_user.user_id)
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "is_tested": is_tested 
    }


# --- [鍮꾨?踰덊샇 李얘린 ?꾨줈?몄뒪] ---

@router.post("/password-recovery/send-code", response_model=Msg)
async def send_recovery_code(
    email_in: PasswordRecoveryEmail, 
    db: Session = Depends(get_db)
):
    """
    1 ?④퀎 - 肄붾뱶 諛쒖넚: ?대찓??議댁옱 ?뺤씤 ??6?먮━ ?몄쬆 肄붾뱶瑜?硫붿씪濡?蹂대깂
    """
    user = user_crud.get_user_by_email(db, email=email_in.email)
    if not user:
        raise HTTPException(status_code=404, detail="?좎?瑜?李얠쓣 ???놁뒿?덈떎.")

    # 1. 6?먮━ ?쒕뜡 ?レ옄 ?앹꽦
    reset_code = f"{secrets.randbelow(1000000):06d}"
    
    # 2. DB ?좎? 媛앹껜??肄붾뱶? 留뚮즺?쒓컙(10遺? 湲곕줉
    user.reset_code = reset_code
    user.reset_code_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.commit()

    # 3. ?대찓??硫붿떆吏 援ъ꽦 (Pylance recipients ?먮윭 諛⑹?瑜??꾪빐 cast ?ъ슜)
    message = MessageSchema(
        subject="[VIPA] 鍮꾨?踰덊샇 ?ъ꽕???몄쬆 肄붾뱶",
        recipients=cast(Any, [str(user.email)]), 
        body=f"?몄쬆 肄붾뱶: [{reset_code}]\n10遺??대궡???낅젰??二쇱꽭??",
        subtype=MessageType.plain
    )

    # 4. fastmail ?몄뒪?댁뒪瑜??듯븳 鍮꾨룞湲?硫붿씪 諛쒖넚
    await fastmail.send_message(message)
    
    return {"message": "?몄쬆 肄붾뱶媛 ?대찓?쇰줈 諛쒖넚?섏뿀?듬땲??"}


@router.post("/password-recovery/verify-code", response_model=Msg)
def verify_recovery_code(verify_in: VerifyRecoveryCode, db: Session = Depends(get_db)):
    """
    2 ?④퀎 - 肄붾뱶 寃利? ?낅젰??肄붾뱶媛 DB??肄붾뱶? ?쇱튂?섎뒗吏, 留뚮즺?섏????딆븯?붿? ?뺤씤??
    """
    user = user_crud.get_user_by_email(db, email=verify_in.email)
    if not user:
        raise HTTPException(status_code=404, detail="?좎?瑜?李얠쓣 ???놁뒿?덈떎.")

    # 1. 肄붾뱶 ?쇱튂 ?щ? 寃??(SQLAlchemy Column 鍮꾧탳 ?먮윭 諛⑹?瑜??꾪빐 cast)
    if not cast(bool, user.reset_code == verify_in.code):
        raise HTTPException(status_code=400, detail="?몄쬆 肄붾뱶媛 ?쇱튂?섏? ?딆뒿?덈떎.")

    # 2. ?쒓컙 留뚮즺 ?щ? 寃??
    now = datetime.now(timezone.utc)
    if user.reset_code_expires_at and now > user.reset_code_expires_at:
        raise HTTPException(status_code=400, detail="?몄쬆 肄붾뱶媛 留뚮즺?섏뿀?듬땲??")

    return {"message": "?몄쬆???깃났?덉뒿?덈떎. ?덈줈??鍮꾨?踰덊샇濡?蹂寃쏀빐 二쇱꽭??"}


@router.patch("/password-recovery/reset", response_model=Msg)
def reset_password(reset_in: ResetPassword, db: Session = Depends(get_db)):
    """
    3 ?④퀎 - 鍮꾨?踰덊샇 蹂寃? ?몄쬆???뺣낫瑜?諛뷀깢?쇰줈 ?덈줈??鍮꾨?踰덊샇瑜??댁떛?섏뿬 ??ν븿.
    """
    user = user_crud.get_user_by_email(db, email=reset_in.email)
    if not user:
        raise HTTPException(status_code=404, detail="?좎?瑜?李얠쓣 ???놁뒿?덈떎.")

    # 1. 蹂댁븞???꾪븳 ?ш?利?(肄붾뱶 ?쇱튂 諛??쒓컙 ?뺤씤)
    if not cast(bool, user.reset_code == reset_in.code):
        raise HTTPException(status_code=400, detail="?좏슚?섏? ?딆? ?몄쬆 肄붾뱶?낅땲??")
    
    now = datetime.now(timezone.utc)
    if user.reset_code_expires_at and now > user.reset_code_expires_at:
        raise HTTPException(status_code=400, detail="?몄쬆 ?쒓컙??珥덇낵?섏뿀?듬땲??")

    # 2. ?덈줈??鍮꾨?踰덊샇 ?댁떛 諛??낅뜲?댄듃
    user.password = cast(Any, security.get_password_hash(reset_in.new_password))
    
    # 3. ?ъ슜 ?꾨즺???몄쬆 肄붾뱶 珥덇린??(蹂댁븞???꾩닔)
    user.reset_code = None
    user.reset_code_expires_at = None
    
    db.commit()

    return {"message": "鍮꾨?踰덊샇媛 ?깃났?곸쑝濡?蹂寃쎈릺?덉뒿?덈떎."}



# -- 鍮꾨?踰덊샇 ?ъ꽕??(?몄쬆???좎??? ---


@router.patch("/mypage/change-password")
def change_password(
    data: PasswordChangeRequest, 
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id) # ?대? ???뺤쓽?섏뼱 ?덉쓬
):
    # 1. DB?먯꽌 ?좎? 議고쉶 (db_user媛 None?????덉쓬???몄?)
    db_user = db.query(User).filter(User.user_id == user_id).first()
    
    # 2. ?좎?媛 ?놁쓣 寃쎌슦 Null 泥댄겕 (Pylance ?먮윭 ?닿껐)
    if not db_user:
        raise HTTPException(status_code=404, detail="?좎?瑜?李얠쓣 ???놁뒿?덈떎.")
    
    # 3. 湲곗〈 鍮꾨?踰덊샇 寃利?(db_user.password媛 None??寃쎌슦瑜??鍮꾪빐 str()濡?罹먯뒪??
    if not security.verify_password(data.old_password, str(db_user.password)):
        raise HTTPException(status_code=400, detail="湲곗〈 鍮꾨?踰덊샇媛 ?쇱튂?섏? ?딆뒿?덈떎.")
    
    # 4. ?덈줈??鍮꾨?踰덊샇 ?댁떛 諛????
    db_user.password = security.get_password_hash(data.new_password)
    db.commit()
    
    return {"message": "鍮꾨?踰덊샇媛 蹂寃쎈릺?덉뒿?덈떎."}


# --- [?뚯썝 ?덊눜] ---
@router.delete("/withdraw", response_model=Msg)
def withdraw_user(
    db: Session = Depends(get_db),
    # 1. ?ш린???좏겙??寃利앺븯怨?user_id瑜?諛붾줈 異붿텧?⑸땲??
    user_id: int = Depends(get_current_user_id) 
):
    """
    ?뚯썝 ?덊눜 API:
    JWT ?좏겙?먯꽌 異붿텧??user_id瑜??ъ슜?섏뿬 怨꾩젙????젣?⑸땲??
    """
    try:
        # 2. 異붿텧??user_id瑜???젣 濡쒖쭅???꾨떖
        user_crud.delete_user(db=db, user_id=user_id)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="?뚯썝 ?덊눜 泥섎━ 以??ㅻ쪟媛 諛쒖깮?덉뒿?덈떎."
        )
    
    return {"message": "怨꾩젙???깃났?곸쑝濡???젣?섏뿀?듬땲??"}


# --- [프로필 업데이트] ---

# 의존성 주입을 위한 인스턴스 생성 헬퍼
def get_storage_service():
    return SupabaseStorageService()

@router.patch("/me/profile", response_model=UserResponse)
async def update_my_profile(
    nickname: str | None = Form(None),
    profile_image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    [API] 프로필(닉네임 및 이미지) 수정 엔드포인트
    - 기능: 유저 검증, 닉네임 중복 체크를 수행한 후 이미지가 존재하면 Supabase Cloud 스토리지에 저장하고 그 URL을 DB에 기록합니다.
    """
    # 1. 대상 유저 검증
    current_user = user_crud.get_user_by_id(db, user_id=user_id)
    if not current_user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")

    # 2. 닉네임 변경 시 중복 검사
    if nickname and nickname != current_user.nickname:
        existing_user = user_crud.get_user_by_nickname(db, nickname=nickname)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="이미 사용 중인 닉네임입니다."
            )

    # 3. 이미지 업로드 로직 수행
    image_url = current_user.profile_image
    if profile_image:
        try:
            storage_service = get_storage_service()
            # 로컬 디스크가 아닌 Supabase Storage로 직접 업로드하고 스토리지 주소(https://...)를 받아옵니다.
            image_url = await storage_service.save_file(profile_image, folder="avatar")
        except RuntimeError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    # 4. 데이터베이스 트랜잭션 갱신
    try:
        updated_user = user_crud.update_user_profile(
            db=db, 
            user_id=user_id, 
            nickname=nickname, 
            profile_image=image_url
        )
        return updated_user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="데이터베이스 갱신 중 오류가 발생했습니다."
        )