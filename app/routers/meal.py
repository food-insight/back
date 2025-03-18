from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db, cache
from models.meal import Meal
from models.food import Food
from services.food_recognition_service import recognize_food_from_image
from services.nutrition_analysis import analyze_meal_nutrition
from app.helpers.meal_helper import process_meal_image, save_meal_image
from utils.responses import success_response, error_response
from werkzeug.utils import secure_filename
import os
import uuid
import datetime

meal_bp = Blueprint('meal', __name__)

@meal_bp.route('/', methods=['POST'])
@jwt_required()
def create_meal():
    """식사 기록 추가 API - 텍스트 및 이미지 업로드 지원"""
    current_user_id = get_jwt_identity()

    # 폼 데이터 또는 JSON 처리
    if request.content_type and 'multipart/form-data' in request.content_type:
        # 폼 데이터 처리
        meal_time = request.form.get('meal_time')
        content = request.form.get('content')
        date_str = request.form.get('date')
        food_names = request.form.getlist('food_names[]')

        # 이미지 처리
        image_path = None
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file.filename:
                # 이미지 저장
                image_path = save_meal_image(image_file)

                # 이미지에서 음식 인식 (사용자가 음식을 명시하지 않은 경우)
                if not food_names and image_path:
                    try:
                        detected_foods = recognize_food_from_image(image_path)
                        food_names = detected_foods
                    except Exception as e:
                        current_app.logger.error(f"음식 인식 오류: {str(e)}")
    else:
        # JSON 데이터 처리
        data = request.get_json()
        meal_time = data.get('meal_time')
        content = data.get('content')
        date_str = data.get('date')
        food_names = data.get('food_names', [])
        image_path = None

    # 필수 필드 검증
    if not meal_time:
        return error_response('meal_time 필드가 필요합니다.', 400)

    # 날짜 처리
    date = None
    if date_str:
        try:
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return error_response('날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식이어야 합니다.', 400)
    else:
        date = datetime.datetime.now().date()

    try:
        # 식사 기록 생성
        meal = Meal(
            uid=current_user_id,
            meal_time=meal_time,
            content=content,
            date=date,
            image_path=image_path
        )
        db.session.add(meal)
        db.session.flush()  # ID 생성을 위해 flush

        # 음식 정보 추가
        for food_name in food_names:
            food = Food(mid=meal.mid, food_name=food_name)
            db.session.add(food)

        db.session.commit()

        # 캐시 무효화
        cache.delete(f'user_{current_user_id}_meals')

        # 식사 영양 분석
        nutrition_data = None
        if food_names:
            try:
                nutrition_data = analyze_meal_nutrition(food_names)
            except Exception as e:
                current_app.logger.error(f"영양 분석 오류: {str(e)}")

        return success_response({
            'message': '식사 기록이 성공적으로 추가되었습니다.',
            'meal': meal.to_dict(),
            'nutrition': nutrition_data
        }, 201)
    except Exception as e:
        db.session.rollback()
        return error_response(f'식사 기록 추가 실패: {str(e)}', 500)

@meal_bp.route('/speech', methods=['POST'])
@jwt_required()
def create_meal_from_speech():
    """음성으로 식사 기록 추가 API"""
    current_user_id = get_jwt_identity()

    # 음성 파일 확인
    if 'audio' not in request.files:
        return error_response('음성 파일이 필요합니다.', 400)

    audio_file = request.files['audio']
    if not audio_file.filename:
        return error_response('음성 파일이 선택되지 않았습니다.', 400)

    # 파일 확장자 확인
    ext = audio_file.filename.rsplit('.', 1)[1].lower() if '.' in audio_file.filename else ''
    if ext not in current_app.config['ALLOWED_AUDIO_EXTENSIONS']:
        return error_response('허용되지 않은 파일 형식입니다.', 400)

    try:
        # 음성 파일 저장
        filename = secure_filename(f"{uuid.uuid4()}.{ext}")
        audio_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'audio', filename)
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        audio_file.save(audio_path)

        # 음성을 텍스트로 변환 및 식사 정보 추출
        from services.speech_to_text import process_speech
        meal_data = process_speech(audio_path)

        if not meal_data:
            return error_response('음성에서 식사 정보를 추출할 수 없습니다.', 400)

        # 식사 기록 생성
        meal = Meal(
            uid=current_user_id,
            meal_time=meal_data.get('meal_time', '기타'),
            content=meal_data.get('content', ''),
            date=datetime.datetime.now().date()
        )
        db.session.add(meal)
        db.session.flush()

        # 음식 정보 추가
        for food_name in meal_data.get('food_names', []):
            food = Food(mid=meal.mid, food_name=food_name)
            db.session.add(food)

        db.session.commit()

        # 영양 분석
        nutrition_data = None
        if 'food_names' in meal_data and meal_data['food_names']:
            nutrition_data = analyze_meal_nutrition(meal_data['food_names'])

        return success_response({
            'message': '음성으로 식사 기록이 성공적으로 추가되었습니다.',
            'meal': meal.to_dict(),
            'nutrition': nutrition_data
        }, 201)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"음성 처리 오류: {str(e)}")
        return error_response(f'음성 처리 실패: {str(e)}', 500)
    finally:
        # 임시 파일 삭제
        if 'audio_path' in locals() and os.path.exists(audio_path):
            os.remove(audio_path)

@meal_bp.route('/', methods=['GET'])
@jwt_required()
@cache.cached(timeout=300, key_prefix=lambda: f'user_{get_jwt_identity()}_meals')
def get_meals():
    """사용자의 식사 기록 조회 API"""
    current_user_id = get_jwt_identity()

    # 필터링 파라미터
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    meal_time = request.args.get('meal_time')
    limit = int(request.args.get('limit', 10))
    page = int(request.args.get('page', 1))

    query = Meal.query.filter_by(uid=current_user_id)

    # 날짜 필터링
    if start_date:
        try:
            start = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Meal.date >= start)
        except ValueError:
            return error_response('시작 날짜 형식이 올바르지 않습니다.', 400)

    if end_date:
        try:
            end = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Meal.date <= end)
        except ValueError:
            return error_response('종료 날짜 형식이 올바르지 않습니다.', 400)

    # 식사 시간 필터링
    if meal_time:
        query = query.filter_by(meal_time=meal_time)

    # 페이지네이션
    total_count = query.count()
    total_pages = (total_count + limit - 1) // limit
    query = query.order_by(Meal.date.desc(), Meal.mid.desc())
    meals = query.offset((page - 1) * limit).limit(limit).all()

    return success_response({
        'meals': [meal.to_dict() for meal in meals],
        'pagination': {
            'total_count': total_count,
            'total_pages': total_pages,
            'current_page': page,
            'limit': limit
        }
    })

@meal_bp.route('/<int:meal_id>', methods=['GET'])
@jwt_required()
def get_meal(meal_id):
    """특정 식사 기록 조회 API"""
    current_user_id = get_jwt_identity()

    meal = Meal.query.filter_by(mid=meal_id, uid=current_user_id).first()

    if not meal:
        return error_response('식사 기록을 찾을 수 없습니다.', 404)

    # 영양 분석 데이터 가져오기
    food_names = [food.food_name for food in meal.foods]
    nutrition_data = None
    if food_names:
        try:
            nutrition_data = analyze_meal_nutrition(food_names)
        except Exception as e:
            current_app.logger.error(f"영양 분석 오류: {str(e)}")

    return success_response({
        'meal': meal.to_dict(),
        'nutrition': nutrition_data
    })

@meal_bp.route('/<int:meal_id>', methods=['PUT'])
@jwt_required()
def update_meal(meal_id):
    """식사 기록 업데이트 API"""
    current_user_id = get_jwt_identity()

    meal = Meal.query.filter_by(mid=meal_id, uid=current_user_id).first()
    if not meal:
        return error_response('식사 기록을 찾을 수 없습니다.', 404)

    data = request.get_json()

    try:
        if 'meal_time' in data:
            meal.meal_time = data['meal_time']
        if 'content' in data:
            meal.content = data['content']
        if 'date' in data:
            try:
                meal.date = datetime.datetime.strptime(data['date'], '%Y-%m-%d').date()
            except ValueError:
                return error_response('날짜 형식이 올바르지 않습니다.', 400)

        # 음식 업데이트
        if 'food_names' in data:
            # 기존 음식 삭제
            Food.query.filter_by(mid=meal_id).delete()

            # 새 음식 추가
            for food_name in data['food_names']:
                food = Food(mid=meal_id, food_name=food_name)
                db.session.add(food)

        db.session.commit()

        # 캐시 무효화
        cache.delete(f'user_{current_user_id}_meals')

        # 영양 분석 갱신
        nutrition_data = None
        food_names = [food.food_name for food in meal.foods]
        if food_names:
            try:
                nutrition_data = analyze_meal_nutrition(food_names)
            except Exception as e:
                current_app.logger.error(f"영양 분석 오류: {str(e)}")

        return success_response({
            'message': '식사 기록이 성공적으로 업데이트되었습니다.',
            'meal': meal.to_dict(),
            'nutrition': nutrition_data
        })
    except Exception as e:
        db.session.rollback()
        return error_response(f'식사 기록 업데이트 실패: {str(e)}', 500)

@meal_bp.route('/<int:meal_id>', methods=['DELETE'])
@jwt_required()
def delete_meal(meal_id):
    """식사 기록 삭제 API"""
    current_user_id = get_jwt_identity()

    meal = Meal.query.filter_by(mid=meal_id, uid=current_user_id).first()
    if not meal:
        return error_response('식사 기록을 찾을 수 없습니다.', 404)

    try:
        # 연결된 음식 정보 삭제
        Food.query.filter_by(mid=meal_id).delete()

        # 식사 이미지가 있으면 삭제
        if meal.image_path and os.path.exists(meal.image_path):
            os.remove(meal.image_path)

        # 식사 기록 삭제
        db.session.delete(meal)
        db.session.commit()

        # 캐시 무효화
        cache.delete(f'user_{current_user_id}_meals')

        return success_response({
            'message': '식사 기록이 성공적으로 삭제되었습니다.'
        })
    except Exception as e:
        db.session.rollback()
        return error_response(f'식사 기록 삭제 실패: {str(e)}', 500)

@meal_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_meal_stats():
    """식사 통계 API"""
    current_user_id = get_jwt_identity()

    # 기간 필터
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # 기본 기간: 지난 30일
    if not start_date:
        start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.datetime.now().strftime('%Y-%m-%d')

    try:
        start = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return error_response('날짜 형식이 올바르지 않습니다.', 400)

    # 식사 기록 조회
    meals = Meal.query.filter(
        Meal.uid == current_user_id,
        Meal.date >= start,
        Meal.date <= end
    ).all()

    # 통계 계산
    meal_counts = {}
    daily_counts = {}
    food_frequency = {}

    for meal in meals:
        # 식사 시간별 통계
        meal_counts[meal.meal_time] = meal_counts.get(meal.meal_time, 0) + 1

        # 날짜별 통계
        date_str = meal.date.strftime('%Y-%m-%d')
        daily_counts[date_str] = daily_counts.get(date_str, 0) + 1

        # 음식 빈도 통계
        for food in meal.foods:
            food_frequency[food.food_name] = food_frequency.get(food.food_name, 0) + 1

    # 가장 자주 먹는 음식 Top 5
    top_foods = sorted(food_frequency.items(), key=lambda x: x[1], reverse=True)[:5]

    return success_response({
        'period': {
            'start_date': start_date,
            'end_date': end_date,
            'total_days': (end - start).days + 1
        },
        'meal_time_stats': meal_counts,
        'daily_meal_counts': daily_counts,
        'top_foods': [{'name': name, 'count': count} for name, count in top_foods],
        'total_meals': len(meals)
    })