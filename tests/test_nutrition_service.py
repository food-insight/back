import pytest
from fastapi.testclient import TestClient
import os
import sys
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# API 앱 임포트
try:
    from app.main import app
except ImportError:
    # 모듈 레벨 건너뛰기 대신 app 변수에 None 할당
    app = None

# 앱 가져오기 실패 시 모든 테스트를 건너뛰기 위한 픽스처
@pytest.fixture(scope="session", autouse=True)
def check_app():
    if app is None:
        pytest.skip("API 앱을 임포트할 수 없습니다. app/main.py 파일이 존재하는지 확인하세요.", allow_module_level=True)

# 테스트 클라이언트 설정
@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


class TestAPIIntegration:
    """API 통합 테스트"""

    def test_full_user_flow(self, client):
        """사용자 흐름 전체 테스트"""
        # 테스트 사용자 ID
        user_id = "test_integration_user"

        # 1. 음식 인식 테스트
        recognition_response = client.post(
            "/api/foods/recognize",
            json={"text": "오늘 점심으로 닭가슴살 샐러드와 현미밥을 먹었어요"}
        )
        assert recognition_response.status_code == 200
        recognized_foods = recognition_response.json().get("foods", [])
        assert len(recognized_foods) > 0

        # 2. 영양 분석 테스트
        nutrition_response = client.post(
            "/api/nutrition/analyze",
            json={"foods": recognized_foods}
        )
        assert nutrition_response.status_code == 200
        nutrition_result = nutrition_response.json()
        assert "calories" in nutrition_result

        # 3. 식사 기록 테스트
        meal_log_response = client.post(
            "/api/meals/log",
            json={
                "user_id": user_id,
                "foods": [{"name": food, "serving_size": "1인분", "quantity": 1.0} for food in recognized_foods],
                "meal_type": "점심",
                "meal_time": datetime.now().isoformat()
            }
        )
        assert meal_log_response.status_code == 200

        # 4. 건강 목표 진행 상황 확인 테스트
        progress_response = client.get(f"/api/users/{user_id}/health-progress")
        assert progress_response.status_code == 200
        progress_result = progress_response.json()
        assert "health_goal" in progress_result

        # 5. 개인화된 추천 테스트
        recommendations_response = client.post(
            "/api/recommendations",
            json={
                "user_id": user_id,
                "food_preference": ["한식", "고단백"],
                "exclude_foods": [],
                "meal_type": "저녁"
            }
        )
        assert recommendations_response.status_code == 200
        recommendations_result = recommendations_response.json()
        assert "meal_recommendations" in recommendations_result

    def test_image_recognition_flow(self, client):
        """이미지 인식 흐름 테스트"""
        import os

        # 테스트 이미지 파일 경로 확인
        image_path = os.path.join(os.path.dirname(__file__), "test_data", "test_food_image.jpg")

        # 테스트 데이터 디렉토리가 없는 경우 생성
        os.makedirs(os.path.join(os.path.dirname(__file__), "test_data"), exist_ok=True)

        # 이미지 파일이 없으면 테스트용 이미지 생성 또는 테스트 건너뛰기
        if not os.path.exists(image_path):
            try:
                # 간단한 테스트 이미지 생성 시도
                from PIL import Image
                img = Image.new('RGB', (100, 100), color = (73, 109, 137))
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                img.save(image_path)
                print(f"테스트 이미지 생성됨: {image_path}")
            except Exception as e:
                pytest.skip(f"테스트 이미지 파일을 생성할 수 없습니다: {e}")
                return

        # 이미지 업로드 테스트
        with open(image_path, "rb") as image_file:
            response = client.post(
                "/api/foods/recognize",
                files={"image": ("test_image.jpg", image_file, "image/jpeg")},
                data={"text": ""}  # 텍스트 필드는 비워둠
            )

        assert response.status_code == 200
        result = response.json()
        assert "foods" in result
        assert len(result["foods"]) > 0

    def test_chatbot_conversation_flow(self, client):
        """챗봇 대화 흐름 테스트"""
        user_id = "test_chat_user"

        # 1. 초기 질문
        first_response = client.post(
            "/api/chat",
            json={
                "user_id": user_id,
                "message": "건강한 아침 식사 추천해줘"
            }
        )

        # API 키가 없거나 서비스 사용 불가시 테스트 건너뛰기
        if first_response.status_code == 503:
            pytest.skip("챗봇 서비스를 사용할 수 없어 테스트를 건너뜁니다.")

        assert first_response.status_code == 200
        first_result = first_response.json()
        assert "response" in first_result

        # 2. 후속 질문 (대화 맥락 유지 테스트)
        second_response = client.post(
            "/api/chat",
            json={
                "user_id": user_id,
                "message": "고단백 저탄수화물로 변경해줘"
            }
        )
        assert second_response.status_code == 200
        second_result = second_response.json()
        assert "response" in second_result

        # 3. 영양 관련 구체적 질문
        third_response = client.post(
            "/api/chat",
            json={
                "user_id": user_id,
                "message": "단백질이 많은 채식 음식은 뭐가 있어?"
            }
        )
        assert third_response.status_code == 200
        third_result = third_response.json()
        assert "response" in third_result


class TestErrorHandling:
    """오류 처리 테스트"""

    def test_invalid_food_recognition_request(self, client):
        """잘못된 음식 인식 요청 테스트"""
        # 텍스트와 이미지 모두 없는 경우
        response = client.post(
            "/api/foods/recognize",
            json={"text": None}
        )
        assert response.status_code == 400  # Bad Request

        # 잘못된 형식의 요청
        response = client.post(
            "/api/foods/recognize",
            json={"invalid_key": "some_value"}
        )
        assert response.status_code in [400, 422]  # Bad Request 또는 Unprocessable Entity

    def test_invalid_user_id(self, client):
        """잘못된 사용자 ID 테스트"""
        response = client.get("/api/users/non_existent_user/health-progress")
        assert response.status_code in [404, 400]  # Not Found 또는 Bad Request

        response = client.post(
            "/api/recommendations",
            json={"user_id": ""}  # 빈 사용자 ID
        )
        assert response.status_code in [400, 422]  # Bad Request 또는 Unprocessable Entity

    def test_invalid_meal_log(self, client):
        """잘못된 식사 기록 테스트"""
        # 필수 필드 누락
        response = client.post(
            "/api/meals/log",
            json={
                "user_id": "test_user",
                # 음식 목록 누락
                "meal_type": "점심",
                "meal_time": datetime.now().isoformat()
            }
        )
        assert response.status_code in [400, 422]  # Bad Request 또는 Unprocessable Entity

        # 잘못된 날짜 형식
        response = client.post(
            "/api/meals/log",
            json={
                "user_id": "test_user",
                "foods": [{"name": "닭가슴살", "serving_size": "100g", "quantity": 1.0}],
                "meal_type": "점심",
                "meal_time": "invalid-date-format"
            }
        )
        assert response.status_code in [400, 422]  # Bad Request 또는 Unprocessable Entity


if __name__ == "__main__":
    pytest.main(["-v", __file__])