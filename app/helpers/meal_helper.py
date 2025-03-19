import os
import uuid
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app
from services import service_manager

logger = logging.getLogger(__name__)

def save_meal_image(image_file, user_id=None):
    """식사 이미지 저장 함수"""
    try:
        # 파일 이름 안전하게 저장
        original_filename = secure_filename(image_file.filename)

        # 파일 확장자 추출
        _, file_extension = os.path.splitext(original_filename)

        # 고유한 파일 이름 생성
        unique_filename = f"{user_id}_{uuid.uuid4().hex}{file_extension}" if user_id else f"{uuid.uuid4().hex}{file_extension}"

        # 업로드 경로 생성
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'meals')
        os.makedirs(upload_dir, exist_ok=True)

        # 파일 저장 경로
        file_path = os.path.join(upload_dir, unique_filename)

        # 파일 저장
        image_file.save(file_path)

        # 상대 경로 반환 (API에서 접근 가능한 URL)
        relative_path = os.path.join('uploads', 'meals', unique_filename)

        logger.info(f"이미지 저장 성공: {relative_path}")

        return {
            'success': True,
            'file_path': file_path,
            'relative_path': relative_path
        }

    except Exception as e:
        logger.error(f"이미지 저장 중 오류 발생: {str(e)}")
        return {'success': False, 'error': str(e)}

def process_meal_image(image_file, user_id=None):
    """식사 이미지 처리 함수"""
    try:
        # 이미지 저장
        save_result = save_meal_image(image_file, user_id)

        if not save_result['success']:
            return {'success': False, 'error': save_result['error']}

        # 음식 인식 서비스 호출
        recognition_service = service_manager.get_service('recognition')
        recognition_result = recognition_service.process_food_image(save_result['file_path'])

        # 인식 결과와 이미지 경로 반환
        return {
            'success': True,
            'foods': recognition_result[0],  # 인식된 음식 목록
            'processed_image': recognition_result[1],  # 처리된 이미지 경로 (있을 경우)
            'original_image': save_result['relative_path']  # 원본 이미지 상대 경로
        }

    except Exception as e:
        logger.error(f"식사 이미지 처리 중 오류 발생: {str(e)}")
        return {'success': False, 'error': str(e)}

def create_meal_record(user_id, meal_data):
    """식사 기록 생성 함수"""
    try:
        # 현재 시간
        now = datetime.now()

        # 기본 식사 기록 정보
        meal_record = {
            'user_id': user_id,
            'datetime': now.isoformat(),
            'meal_type': meal_data.get('meal_type', '기타'),
            'foods': meal_data.get('foods', []),
            'notes': meal_data.get('notes', ''),
            'images': meal_data.get('images', [])
        }

        # 영양 정보 계산
        nutrition_info = calculate_meal_nutrition(meal_record['foods'])
        meal_record['nutrition'] = nutrition_info

        # 데이터베이스에 저장 (서비스 사용)
        meal_service = service_manager.get_service('meal')
        result = meal_service.add_meal_record(meal_record)

        return {'success': True, 'meal_id': result['meal_id']}

    except Exception as e:
        logger.error(f"식사 기록 생성 중 오류 발생: {str(e)}")
        return {'success': False, 'error': str(e)}

def calculate_meal_nutrition(foods):
    """식사의 영양 정보 계산 함수"""
    try:
        # 초기 영양 정보
        nutrition = {
            'calories': 0,
            'carbs': 0,
            'protein': 0,
            'fat': 0,
            'sodium': 0,
            'sugar': 0,
            'fiber': 0
        }

        # 영양 서비스 가져오기
        nutrition_service = service_manager.get_service('nutrition')

        # 각 음식별 영양 정보 합산
        for food in foods:
            food_name = food.get('name', '')
            quantity = food.get('quantity', 100)
            unit = food.get('unit', 'g')

            # 음식 영양 정보 조회
            food_nutrition = nutrition_service.analyze_food_nutrients(food_name, quantity, unit)

            # 합산
            for key in nutrition:
                nutrition[key] += food_nutrition.get(key, 0)

        return nutrition

    except Exception as e:
        logger.error(f"식사 영양 정보 계산 중 오류 발생: {str(e)}")
        return {}