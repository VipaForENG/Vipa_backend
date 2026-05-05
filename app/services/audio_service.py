import os
import uuid
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.conversation_session import ConversationSession

# 오디오 저장 경로 설정
UPLOAD_DIR = "static/audio"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

async def save_audio_file(db: Session, session_id: int, file: UploadFile) -> str:
    # 🔥 해결 1: 파일명이 None일 경우를 대비해 기본값("") 설정
    filename = file.filename or ""
    
    # 1. 파일 확장자 체크
    allowed_extensions = ["m4a", "wav", "mp3", "aac"]
    file_ext = filename.split(".")[-1].lower() if "." in filename else ""
    
    if not file_ext or file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="지원하지 않는 오디오 형식입니다.")

    # 2. 유니크한 파일명 생성
    file_name = f"session_{session_id}_{uuid.uuid4().hex[:8]}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    # 3. 파일 물리적 저장
    try:
        content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 저장 중 오류 발생: {str(e)}")

    # 4. DB의 conversation_session 테이블 업데이트
    stmt = select(ConversationSession).where(ConversationSession.session_id == session_id)
    session_record = db.execute(stmt).scalar()
    
    if not session_record:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=404, detail="해당 세션을 찾을 수 없습니다.")

    audio_url = f"/static/audio/{file_name}"
    session_record.audio_url = audio_url  # type: ignore
    
    db.commit()

    return audio_url