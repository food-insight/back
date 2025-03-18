from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from app.extensions import db
from services.food_recognition import recognize_food_from_image
from utils.response import success_response, error_response
from utils.image_processing import is_allowed_image, save_image, process_image
import os
import uuid

image_bp = Blueprint('image', __name__)

@image_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_image():
    """이미지 업로드 API"""
    current_user_id = get_jwt_identity()

    # 이미지 파일 확인
    if 'image' not in request.files:
        return error_response('이미지 파일이 필요합니다.', 400)

    image_file = request.files['image']
    if not image_file.filename:
        return error_response('이미지 파일이 선택되지 않았습니다.', 400)

    # 파일 확장자 검증
    if not is_allowed_image(image_file.filename):
        return error_response('허용되지 않은 파일 형식입니다. (PNG, JPG, JPEG, GIF만 허용)', 400)

    try:
        # 이미지 저장
        filename = secure_filename(f"{uuid.uuid4()}_{image_file.filename}")
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'images', filename)
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        image_file.save(image_path)

        # 이미지 경로 반환
        image_url = f"/api/images/view/{filename}"

        return success_response({
            'message': '이미지가 성공적으로 업로드되었습니다.',
            'image_path': image_path,
            'image_url': image_url,
            'filename': filename
        }, 201)
    except Exception as e:
        current_app.logger.error(f"이미지 업로드 오류: {str(e)}")
        return error_response(f'이미지 업로드 실패: {str(e)}', 500)

@image_bp.route('/view/<filename>', methods=['GET'])
def view_image(filename):
    """이미지 조회 API"""
    try:
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'images', filename)

        if not os.path.exists(image_path):
            return error_response('이미지를 찾을 수 없습니다.', 404)

        return send_file(image_path)
    except Exception as e:
        current_app.logger.error(f"이미지 조회 오류: {str(e)}")
        return error_response(f'이미지 조회 실패: {str(e)}', 500)

@image_bp.route('/food-recognition', methods=['POST'])
@jwt_required()
def food_image_recognition():
    """음식 이미지 인식 API"""
    # 이미지 파일 확인
    if 'image' not in request.files:
        return error_response('이미지 파일이 필요합니다.', 400)

    image_file = request.files['image']
    if not image_file.filename:
        return error_response('이미지 파일이 선택되지 않았습니다.', 400)

    # 파일 확장자 검증
    if not is_allowed_image(image_file.filename):
        return error_response('허용되지 않은 파일 형식입니다. (PNG, JPG, JPEG, GIF만 허용)', 400)

    try:
        # 이미지 저장
        filename = secure_filename(f"food_{uuid.uuid4()}_{image_file.filename}")
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'foods', filename)
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        image_file.save(image_path)

        # 음식 인식 서비스 호출
        recognized_foods = recognize_food_from_image(image_path)

        # 인식된 음식 정보 반환
        return success_response({
            'image_path': image_path,
            'recognized_foods': recognized_foods
        })
    except Exception as e:
        current_app.logger.error(f"음식 인식 오류: {str(e)}")
        return error_response(f'음식 인식 실패: {str(e)}', 500)

@image_bp.route('/meal-photo', methods=['POST'])
@jwt_required()
def process_meal_photo():
    """식사 사진 처리 API - 메인 카메라 촬영 기능"""
    current_user_id = get_jwt_identity()

    # 이미지 파일 확인
    if 'image' not in request.files:
        return error_response('이미지 파일이 필요합니다.', 400)

    image_file = request.files['image']
    if not image_file.filename:
        return error_response('이미지 파일이 선택되지 않았습니다.', 400)

    # 파일 확장자 검증
    if not is_allowed_image(image_file.filename):
        return error_response('허용되지 않은 파일 형식입니다.', 400)

    # 추가 파라미터
    meal_time = request.form.get('meal_time', '기타')
    date_str = request.form.get('date')

    try:
        # 이미지 저장
        filename = secure_filename(f"meal_{uuid.uuid4()}_{image_file.filename}")
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'meals', filename)
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        image_file.save(image_path)

        # 이미지 처리 및 음식 인식
        processed_image_path = process_image(image_path)
        recognized_foods = recognize_food_from_image(processed_image_path)

        # 식사 정보 준비 (실제 저장은 meal 라우트에서 수행)
        meal_data = {
            'image_path': image_path,
            'processed_image_path': processed_image_path,
            'meal_time': meal_time,
            'date': date_str,
            'recognized_foods': recognized_foods
        }

        # 이미지 URL
        image_url = f"/api/images/view/{os.path.basename(image_path)}"
        processed_image_url = f"/api/images/view/{os.path.basename(processed_image_path)}"

        return success_response({
            'message': '식사 사진이 성공적으로 처리되었습니다.',
            'meal_data': meal_data,
            'image_url': image_url,
            'processed_image_url': processed_image_url
        })
    except Exception as e:
        current_app.logger.error(f"식사 사진 처리 오류: {str(e)}")
        return error_response(f'식사 사진 처리 실패: {str(e)}', 500)