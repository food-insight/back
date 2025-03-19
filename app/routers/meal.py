from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import logging
from flask_jwt_extended import jwt_required, get_jwt_identity
from services import service_manager

# Blueprint 정의
meal_bp = Blueprint('meal', __name__)
logger = logging.getLogger(__name__)

# 헬퍼 함수 - 지연 임포트로 순환 참조 방지
def get_meal_helpers():
    from app.helpers.meal_helper import process_meal_image, save_meal_image, create_meal_record
    return process_meal_image, save_meal_image, create_meal_record

@meal_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_meal_image():
    """식사 이미지 업로드 API"""
    try:
        user_id = get_jwt_identity()

        if 'image' not in request.files:
            return jsonify({"error": "이미지 파일이 필요합니다."}), 400

        image_file = request.files['image']

        if image_file.filename == '':
            return jsonify({"error": "선택된 파일이 없습니다."}), 400

        # 파일 확장자 및 MIME 타입 검증
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
        if not image_file.filename.lower().split('.')[-1] in allowed_extensions:
            return jsonify({"error": "지원되지 않는 이미지 형식입니다."}), 400

        # 이미지 처리 (헬퍼 함수 사용)
        process_meal_image, _, _ = get_meal_helpers()
        result = process_meal_image(image_file, user_id)

        if not result.get('success', False):
            return jsonify({"error": result.get('error', '이미지 처리 중 오류가 발생했습니다.')}), 500

        return jsonify({
            "success": True,
            "foods": result.get('foods', []),
            "image_url": result.get('original_image'),
            "processed_image": result.get('processed_image')
        }), 200

    except Exception as e:
        logger.error(f"식사 이미지 업로드 중 오류 발생: {str(e)}")
        return jsonify({"error": "이미지 업로드 중 오류가 발생했습니다."}), 500

@meal_bp.route('/', methods=['POST'])
@jwt_required()
def add_meal_record():
    try:
        user_id = get_jwt_identity()
        data = request.json

        if not data:
            return jsonify({"error": "식사 데이터가 필요합니다."}), 400

        # service_manager를 통해 meal_service 호출
        meal_service = service_manager.get_service('meal')

        # user_id와 data를 모두 전달
        result = meal_service.add_meal_record(
            user_id=user_id,  # 첫 번째 인자로 user_id 전달
            data=data          # 두 번째 인자로 data 전달
        )

        if not result.get('success', False):
            return jsonify({"error": result.get('error', '식사 기록 생성 중 오류가 발생했습니다.')}), 500

        return jsonify({
            "success": True,
            "meal_id": result.get('meal_id'),
            "message": result.get('message')
        }), 201

    except Exception as e:
        logger.error(f"식사 기록 추가 중 오류 발생: {str(e)}")
        return jsonify({"error": "식사 기록 추가 중 오류가 발생했습니다."}), 500

@meal_bp.route('/', methods=['GET'])
@jwt_required()
def get_meal_records():
    """사용자 식사 기록 조회 API"""
    try:
        user_id = get_jwt_identity()

        # 날짜 필터링
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        meal_type = request.args.get('meal_type')

        # 페이징 처리
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))

        # 정렬 옵션
        sort_by = request.args.get('sort_by', 'datetime')
        sort_order = request.args.get('sort_order', 'desc')

        # 식사 기록 서비스 호출
        meal_service = service_manager.get_service('meal')
        result = meal_service.get_user_meals(
            user_id,
            start_date=start_date,
            end_date=end_date,
            meal_type=meal_type,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )

        return jsonify({
            "success": True,
            "meals": result.get('meals', []),
            "total": result.get('total', 0),
            "page": page,
            "limit": limit
        }), 200

    except Exception as e:
        logger.error(f"식사 기록 조회 중 오류 발생: {str(e)}")
        return jsonify({"error": "식사 기록 조회 중 오류가 발생했습니다."}), 500

@meal_bp.route('/<meal_id>', methods=['GET'])
@jwt_required()
def get_meal_detail(meal_id):
    """식사 상세 정보 조회 API"""
    try:
        user_id = get_jwt_identity()

        # 식사 기록 서비스 호출
        meal_service = service_manager.get_service('meal')
        result = meal_service.get_meal_detail(meal_id, user_id)

        if not result.get('success', False):
            return jsonify({"error": result.get('error', '식사 정보를 찾을 수 없습니다.')}), 404

        return jsonify({
            "success": True,
            "meal": result.get('meal', {})
        }), 200

    except Exception as e:
        logger.error(f"식사 상세 정보 조회 중 오류 발생: {str(e)}")
        return jsonify({"error": "식사 정보 조회 중 오류가 발생했습니다."}), 500

@meal_bp.route('/<meal_id>', methods=['PUT'])
@jwt_required()
def update_meal_record(meal_id):
    """식사 기록 수정 API"""
    try:
        user_id = get_jwt_identity()
        data = request.json

        if not data:
            return jsonify({"error": "수정할 식사 데이터가 필요합니다."}), 400

        # 식사 기록 서비스 호출
        meal_service = service_manager.get_service('meal')
        result = meal_service.update_meal_record(meal_id, user_id, data)

        if not result.get('success', False):
            return jsonify({"error": result.get('error', '식사 기록 수정 중 오류가 발생했습니다.')}), 500

        return jsonify({
            "success": True,
            "message": "식사 기록이 성공적으로 수정되었습니다."
        }), 200

    except Exception as e:
        logger.error(f"식사 기록 수정 중 오류 발생: {str(e)}")
        return jsonify({"error": "식사 기록 수정 중 오류가 발생했습니다."}), 500

@meal_bp.route('/<meal_id>', methods=['DELETE'])
@jwt_required()
def delete_meal_record(meal_id):
    """식사 기록 삭제 API"""
    try:
        user_id = get_jwt_identity()

        # 식사 기록 서비스 호출
        meal_service = service_manager.get_service('meal')
        result = meal_service.delete_meal_record(meal_id, user_id)

        if not result.get('success', False):
            return jsonify({"error": result.get('error', '식사 기록 삭제 중 오류가 발생했습니다.')}), 500

        return jsonify({
            "success": True,
            "message": "식사 기록이 성공적으로 삭제되었습니다."
        }), 200

    except Exception as e:
        logger.error(f"식사 기록 삭제 중 오류 발생: {str(e)}")
        return jsonify({"error": "식사 기록 삭제 중 오류가 발생했습니다."}), 500

@meal_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_meal_statistics():
    """식사 통계 API"""
    try:
        user_id = get_jwt_identity()

        # 날짜 필터링
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # 통계 옵션
        group_by = request.args.get('group_by', 'day')  # day, week, month

        # 식사 기록 서비스 호출
        meal_service = service_manager.get_service('meal')
        result = meal_service.get_meal_statistics(
            user_id,
            start_date=start_date,
            end_date=end_date,
            group_by=group_by
        )

        return jsonify({
            "success": True,
            "statistics": result
        }), 200

    except Exception as e:
        logger.error(f"식사 통계 조회 중 오류 발생: {str(e)}")
        return jsonify({"error": "식사 통계 조회 중 오류가 발생했습니다."}), 500