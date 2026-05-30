# app/core/storage.py
import os
import uuid
from abc import ABC, abstractmethod
from fastapi import UploadFile
from supabase import create_client, Client

class BaseStorageService(ABC):
    @abstractmethod
    async def save_file(self, file: UploadFile, folder: str) -> str:
        """파일을 저장하고 접근 가능한 고유 URL을 반환합니다."""
        pass

class SupabaseStorageService(BaseStorageService):
    def __init__(self):
        self.url: str = os.getenv("SUPABASE_URL", "")
        
        # 💡 [핵심 수정] anon_key 대신 service_key를 불러옵니다.
        self.key: str = os.getenv("SUPABASE_SERVICE_KEY", "") 
        self.bucket_name: str = os.getenv("SUPABASE_BUCKET_NAME", "profiles")
        
        # 이제 관리자 권한을 가진 클라이언트가 생성됩니다. (RLS 정책 무시)
        self.client: Client = create_client(self.url, self.key)

    async def save_file(self, file: UploadFile, folder: str) -> str:
        """
        [업로드] 전달받은 UploadFile 자원을 Supabase Storage 버킷에 업로드합니다.
        - 로직 흐름: 파일 확장자 추출 -> UUID 기반 고유 파일명 생성 -> 파일 바이트 읽기 -> Supabase 업로드 -> 공개 URL 반환
        """
        # 1. 파일 이름 검증 및 확장자 분리 (Pylance 정적 분석 에러 방지 안전장치)
        filename = file.filename or ""
        ext = filename.split('.')[-1] if '.' in filename else 'png'
        
        # 2. 버킷 내부에서 중복되지 않도록 고유한 파일 경로 정의 (예: profiles/a1b2c3...png)
        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        storage_path = f"{folder}/{unique_filename}" if folder else unique_filename

        try:
            # 3. 비동기로 파일의 바이너리 데이터 읽기
            file_data = await file.read()
            
            # 4. Supabase Storage API를 호출하여 데이터 업로드
            # content_type을 명시해야 브라우저에서 다운로드되지 않고 바로 이미지가 렌더링됩니다.
            self.client.storage.from_(self.bucket_name).upload(
                path=storage_path,
                file=file_data,
                file_options={"content-type": file.content_type or "image/png"}
            )
            
            # 5. 업로드된 파일의 정적 공개 URL(Public URL)을 생성하여 반환
            public_url = self.client.storage.from_(self.bucket_name).get_public_url(storage_path)
            return public_url

        except Exception as e:
            # 시스템 예외 발생 시 상위 라우터로 전파하여 처리 유도
            raise RuntimeError(f"Supabase Storage 업로드 실패: {str(e)}")
            
        finally:
            # 6. 파일 읽기 작업 완료 후 리소스 해제하여 메모리 누수 방지
            await file.close()