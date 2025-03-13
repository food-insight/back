from flask import current_app
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
from services.food_recognition import recognize_food_from_image
from utils.image_processing import process_image, is_allowed_image

def save_meal_image(image_file):
    """식사 이미지 저장 헬퍼 함수"""
    if not image_file or not image_file.filename:
        return None

    # 파일 형식 검증
    if not is_allowed_image(image_file.filename):
        raise ValueError('허용되지 않은 파일 형식입니다.')

    # 파일명 생성
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filename = secure_filename(f"meal_{timestamp}_{uuid.uuid4()}.{image_file.filename.rsplit('.', 1)[1].lower()}")

    # 저장 경로
    image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'meals', filename)
    os.makedirs(os.path.dirname(image_path), exist_ok=True)

    # 파일 저장
    image_file.save(image_path)

    return image_path

def process_meal_image(image_path):
    """식사 이미지 처리 헬퍼 함수"""
    if not image_path or not os.path.exists(image_path):
        return None, []

    try:
        # 이미지 처리 (리사이징, 품질 개선 등)
        processed_image_path = process_image(image_path)

        # 음식 인식
        recognized_foods = recognize_food_from_image(processed_image_path)

        return processed_image_path, recognized_foods
    except Exception as e:
        current_app.logger.error(f"식사 이미지 처리 오류: {str(e)}")
        return image_path, []

def extract_meal_data_from_text(text):
    """텍스트에서 식사 정보 추출 헬퍼 함수"""
    if not text:
        return None

    # 간단한 규칙 기반 파싱 (실제 구현은 더 복잡할 수 있음)
    meal_data = {
        'food_names': [],
        'meal_time': '기타',
        'content': text
    }

    # 식사 시간 인식
    if '아침' in text or '브런치' in text:
        meal_data['meal_time'] = '아침'
    elif '점심' in text or '런치' in text:
        meal_data['meal_time'] = '점심'
    elif '저녁' in text or '디너' in text:
        meal_data['meal_time'] = '저녁'
    elif '간식' in text or '스낵' in text:
        meal_data['meal_time'] = '간식'

    # 음식 이름 추출 (키워드 기반 단순 추출 - 실제로는 NLP 기법 활용)
    from services.food_recognition import extract_food_names_from_text
    meal_data['food_names'] = extract_food_names_from_text(text)

    return meal_data

def calculate_meal_calories(food_names):
    """식사 칼로리 계산 헬퍼 함수"""
    if not food_names:
        return 0

    try:
        from services.nutrition_analysis import analyze_meal_nutrition
        nutrition_data = analyze_meal_nutrition(food_names)
        return nutrition_data.get('calories', 0)
    except Exception as e:
        current_app.logger.error(f"칼로리 계산 오류: {str(e)}")
        return 0

def generate_meal_summary(meal, nutrition_data=None):
    """식사 요약 생성 헬퍼 함수"""
    if not meal:
        return ''

    foods = []
    try:
        from models.food import Food
        foods = Food.query.filter_by(mid=meal.mid).all()
    except Exception as e:
        current_app.logger.error(f"식사 음식 조회 오류: {str(e)}")

    food_names = [food.food_name for food in foods]
    food_text = ', '.join(food_names) if food_names else '기록된 음식 없음'

    calories = ''
    if nutrition_data and 'calories' in nutrition_data:
        calories = f" (약 {nutrition_data['calories']}kcal)"

    summary = f"{meal.date.strftime('%Y년 %m월 %d일')} {meal.meal_time}: {food_text}{calories}"

    return summary