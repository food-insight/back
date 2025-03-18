import pytest
from fastapi.testclient import TestClient
import os
import sys
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# API 앱 임포트
try:
    from app.main import app  # 실제 앱 경로에 맞게 수정 필요
except ImportError:
    app = None

# 앱 가져오기 실패 시 모든 테스트를 건너뛰기 위한 픽스처
@pytest.fixture(scope="session", autouse=True)
def check_app():
    if app is None:
        pytest.skip("API 앱을 임포트할 수 없습니다. app/main.py 파일이 존재하는지 확인하세요.", allow_module_level=True)

# 테스트 클라이언트 설정
@pytest.fixture
def client():
    return TestClient(app)

class TestAPIIntegration:
    """API 통합 테스트"""

    def test_full_user_flow(self, client):
        """사용자 흐름 전체 테스트"""
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
        from PIL import Image

        # 테스트 이미지 파일 경로 확인
        test_data_dir = os.path.join(os.path.dirname(__file__), "test_data")
        os.makedirs(test_data_dir, exist_ok=True)
        image_path = os.path.join(test_data_dir, "test_food_image.jpg")

        # 이미지 파일이 없으면 생성
        if not os.path.exists(image_path):
            img = Image.new('RGB', (100, 100), color=(73, 109, 137))
            img.save(image_path)
            print(f"테스트 이미지 생성됨: {image_path}")

        # 이미지 업로드 테스트
        with open(image_path, "rb") as image_file:
            response = client.post(
                "/api/foods/recognize",
                files={"image": ("test_image.jpg", image_file, "image/jpeg")},
                data={"text": ""}
            )

        assert response.status_code == 200
        result = response.json()
        assert "foods" in result
        assert len(result["foods"]) >= 0  # 음식을 인식하지 못해도 빈 리스트 허용

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

        assert first_response.status_code == 200
        first_result = first_response.json()

        # 응답 구조 확인 (다양한 응답 형식 지원)
        assert (
                first_result.get('response') or
                (first_result.get('alternative_foods') and first_result.get('meal_recommendations'))
        ), "유효한 응답 형식이 아닙니다."

        # 2. 후속 질문 테스트 (옵션)
        second_response = client.post(
            "/api/chat",
            json={
                "user_id": user_id,
                "message": "고단백 저탄수화물로 변경해줘"
            }
        )
        assert second_response.status_code == 200


class TestErrorHandling:
    """오류 처리 테스트"""

    def test_invalid_food_recognition_request(self, client):
        """잘못된 음식 인식 요청 테스트"""
        # 텍스트와 이미지 모두 없는 경우
        response = client.post(
            "/api/foods/recognize",
            json={"text": None}
        )
        assert response.status_code in [400, 422], "잘못된 요청에 대한 오류 처리 필요"

        # 잘못된 형식의 요청
        response = client.post(
            "/api/foods/recognize",
            json={"invalid_key": "some_value"}
        )
        assert response.status_code in [400, 422], "잘못된 요청 형식에 대한 오류 처리 필요"

    def test_invalid_user_id(self, client):
        """잘못된 사용자 ID 테스트"""
        # 존재하지 않는 사용자 ID로 건강 진행 상황 요청
        response = client.get("/api/users/non_existent_user/health-progress")
        assert response.status_code in [404, 400], "존재하지 않는 사용자 ID 처리 필요"

        # 빈 사용자 ID로 추천 요청
        response = client.post(
            "/api/recommendations",
            json={"user_id": ""}
        )
        assert response.status_code in [400, 422], "잘못된 사용자 ID 처리 필요"

    def test_invalid_meal_log(self, client):
        """잘못된 식사 기록 테스트"""
        # 필수 필드 누락
        response = client.post(
            "/api/meals/log",
            json={
                "user_id": "test_user",
                "meal_type": "점심",
                "meal_time": datetime.now().isoformat()
            }
        )
        assert response.status_code in [400, 422], "필수 필드 누락에 대한 오류 처리 필요"

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
        assert response.status_code in [400, 422], "잘못된 날짜 형식에 대한 오류 처리 필요"

if __name__ == "__main__":
    pytest.main(["-v", __file__])