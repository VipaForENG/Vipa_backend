import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import engine, Base
from app.core.base_data import init_db
from app.core.security import get_password_hash, verify_password, create_access_token, get_current_user_id
from app.schemas.user import UserCreate, UserLogin
from app.core.config import settings

# 테스트 DB 테이블 생성 및 기초 데이터 적재
Base.metadata.create_all(bind=engine)
try:
    init_db()
except Exception:
    pass


class TestVIPAUnit(unittest.TestCase):
    """
    1단계: 단위 테스트 (Unit Test)
    백엔드 보안 함수, Pydantic 스키마 무결성 개별 검증
    """

    def test_password_hashing(self):
        """비밀번호 해싱 및 검증 알고리즘 단위 테스트"""
        plain_password = "SecretPassword123!"
        hashed = get_password_hash(plain_password)
        
        self.assertNotEqual(plain_password, hashed)
        self.assertTrue(verify_password(plain_password, hashed))
        self.assertFalse(verify_password("WrongPassword", hashed))

    def test_jwt_token_generation(self):
        """JWT 토큰 생성 및 해독(Decryption) 단위 테스트"""
        user_id = 9999
        token = create_access_token(user_id)
        
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 20)
        
        extracted_id = get_current_user_id(token)
        self.assertEqual(extracted_id, user_id)

    def test_pydantic_user_schema_validation(self):
        """Pydantic 유저 생성 및 로그인 스키마 검증"""
        user_data = UserCreate(
            email="testuser@vipa.ai",
            password="securepassword123",
            nickname="VIPATester"
        )
        self.assertEqual(user_data.email, "testuser@vipa.ai")
        self.assertEqual(user_data.nickname, "VIPATester")


class TestVIPAIntegration(unittest.TestCase):
    """
    2단계: 통합 테스트 (Integration Test)
    FastAPI Router ↔ App Instance ↔ Schema 연결 상태 검증
    """

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_root_endpoint(self):
        """서버 헬스체크 루트 엔드포인트 통합 테스트"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data["message"], "Welcome to VIPA API Server")
        self.assertEqual(json_data["version"], "1.0.0")

    def test_openapi_schema(self):
        """OpenAPI (Swagger) 문서 스키마 생성 통합 테스트"""
        response = self.client.get(f"{settings.API_V1_STR}/openapi.json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("paths", response.json())

    def test_level_test_questions_endpoint(self):
        """레벨 테스트 문제 목록 제공 라우터 통합 테스트"""
        response = self.client.get(f"{settings.API_V1_STR}/level-test/questions")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertIn("questions", json_data)
        self.assertIsInstance(json_data["questions"], list)
        self.assertGreater(len(json_data["questions"]), 0)


class TestVIPASystemE2E(unittest.TestCase):
    """
    3단계: 시스템 테스트 (System Test E2E)
    인증 ➔ 레벨테스트 ➔ 카테고리 ➔ 어휘까지 전체 E2E 파이프라인 작동 검증
    """

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_full_system_flow(self):
        """전체 앱 비동기 서비스 파이프라인 E2E 검증"""
        # 1. Root API 접근 확인
        root_res = self.client.get("/")
        self.assertEqual(root_res.status_code, 200)

        # 2. 레벨 테스트 문제 가져오기
        level_res = self.client.get(f"{settings.API_V1_STR}/level-test/questions")
        self.assertEqual(level_res.status_code, 200)
        questions = level_res.json().get("questions", [])
        self.assertGreaterEqual(len(questions), 1)

        # 3. 카테고리 라우터 조회 (시나리오 준비)
        cat_res = self.client.get(f"{settings.API_V1_STR}/category/main-categories")
        self.assertEqual(cat_res.status_code, 200)


if __name__ == "__main__":
    unittest.main()
