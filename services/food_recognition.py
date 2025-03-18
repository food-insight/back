# services/food_recognition.py 파일 생성
from services.food_recognition_service import FoodRecognitionService

# FoodRecognitionService 인스턴스 생성
food_recognition_service = FoodRecognitionService()

def recognize_food_from_image(image_data):
    """
    이미지로부터 음식 인식 함수
    FoodRecognitionService의 메서드를 래핑
    """
    return food_recognition_service.recognize_food_from_image(image_data)

def extract_food_names_from_text(text_description):
    """
    텍스트에서 음식 이름 추출 함수

    Args:
        text_description (str): 음식 설명 텍스트

    Returns:
        list: 추출된 음식 이름 목록
    """
    # 기존 코드에서 사용한 한국 음식 목록
    korean_foods = [
        "김치", "불고기", "비빔밥", "떡볶이", "김밥", "라면", "삼겹살", "치킨",
        "된장찌개", "김치찌개", "순두부찌개", "갈비탕", "설렁탕", "불고기", "갈비",
        "잡채", "잔치국수", "냉면", "만두", "제육볶음", "닭갈비", "돼지갈비",
        "김치볶음밥", "오므라이스", "돈까스", "감자탕", "부대찌개", "보쌈", "족발"
    ]

    # 텍스트에 포함된 음식 이름 추출
    food_names = [food for food in korean_foods if food in text_description]

    # 중복 제거
    return list(set(food_names))