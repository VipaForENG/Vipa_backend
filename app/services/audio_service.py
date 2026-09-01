import os
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.storage import SupabaseStorageService
from app.models.conversation_session import ConversationSession

async def save_audio_file(db: Session, session_id: int, file: UploadFile) -> str:
    filename = file.filename or ""

    allowed_extensions = ["m4a", "wav", "mp3", "aac"]
    file_ext = filename.split(".")[-1].lower() if "." in filename else ""

    if not file_ext or file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="지원하지 않는 오디오 형식입니다.")

    try:
        audio_bucket = os.getenv("SUPABASE_AUDIO_BUCKET_NAME", "audio")
        storage_service = SupabaseStorageService(bucket_name=audio_bucket)
        audio_url = await storage_service.save_file(file, folder="audio")

        if not audio_url:
            raise HTTPException(status_code=500, detail="Supabase Storage 업로드에 실패했습니다.")

        stmt = select(ConversationSession).where(ConversationSession.session_id == session_id)
        session_record = db.execute(stmt).scalar()

        if not session_record:
            raise HTTPException(status_code=404, detail="해당 세션을 찾을 수 없습니다.")

        session_record.audio_url = audio_url  # type: ignore
        db.commit()
        return audio_url

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"오디오 업로드 중 오류 발생: {str(e)}")