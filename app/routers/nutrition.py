from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db, cache
from models.meal import Meal
from models.food import Food
from models.user import User
from services.nutrition_analysis import analyze_meal_nutrition, get_nutrition_insights
from services.rag_service import get_nutritional_research
from utils.responses import success_response, error_response
from datetime import datetime, timedelta

nutrition_bp = Blueprint('nutrition', __name__)

@nutrition_bp.route('/analyze/<int:meal_id>', methods=['GET'])
@jwt_required()
def analyze_meal(meal_id):
    """특정 식사의 영양 분석 API"""
    current_user_id = get_jwt_identity()

    # 식사 기록 확인
    meal = Meal.query.filter_by(mid=meal_id, uid=current_user_id).first()
    if not meal:
        return error_response('식사 기록을 찾을 수 없습니다.', 404)

    # 음식 목록 가져오기
    foods = Food.query.filter_by(mid=meal_id).all()
    if not foods:
        return error_response('이 식사에는 등록된 음식이 없습니다.', 404)

    food_names = [food.food_name for food in foods]

    try:
        # 영양 분석
        nutrition_data = analyze_meal_nutrition(food_names)

        # 사용자 정보 가져오기 (나이, 성별 등에 따른 권장 섭취량 계산을 위해)
        user = User.query.filter_by(uid=current_user_id).first()

        # 영양 인사이트 생성
        insights = get_nutrition_insights(nutrition_data, user)

        return success_response({
            'meal': meal.to_dict(),
            'nutrition': nutrition_data,
            'insights': insights
        })
    except Exception as e:
        current_app.logger.error(f"영양 분석 오류: {str(e)}")
        return error_response(f'영양 분석 실패: {str(e)}', 500)

@nutrition_bp.route('/daily', methods=['GET'])
@jwt_required()
def get_daily_nutrition():
    """일일 영양 섭취 분석 API"""
    current_user_id = get_jwt_identity()

    # 날짜 파라미터 (기본: 오늘)
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))

    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return error_response('날짜 형식이 올바르지 않습니다.', 400)

    # 해당 날짜의 모든 식사 조회
    meals = Meal.query.filter_by(
        uid=current_user_id,
        date=target_date
    ).all()

    if not meals:
        return success_response({
            'date': date_str,
            'message': '해당 날짜에 기록된 식사가 없습니다.',
            'total_nutrition': {},
            'meals': []
        })

    # 모든 식사의 음식 집계
    all_foods = []
    meal_data = []

    for meal in meals:
        foods = Food.query.filter_by(mid=meal.mid).all()
        food_names = [food.food_name for food in foods]

        if food_names:
            all_foods.extend(food_names)
            try:
                nutrition = analyze_meal_nutrition(food_names)
                meal_data.append({
                    'meal': meal.to_dict(),
                    'nutrition': nutrition
                })
            except Exception as e:
                current_app.logger.error(f"식사 영양 분석 오류: {str(e)}")
                meal_data.append({
                    'meal': meal.to_dict(),
                    'nutrition': None
                })

    # 전체 영양 분석
    total_nutrition = {}
    if all_foods:
        try:
            total_nutrition = analyze_meal_nutrition(all_foods)
        except Exception as e:
            current_app.logger.error(f"전체 영양 분석 오류: {str(e)}")

    # 사용자 정보 가져오기
    user = User.query.filter_by(uid=current_user_id).first()

    # 영양 인사이트 생성
    insights = get_nutrition_insights(total_nutrition, user)

    return success_response({
        'date': date_str,
        'total_nutrition': total_nutrition,
        'meals': meal_data,
        'insights': insights
    })

@nutrition_bp.route('/weekly', methods=['GET'])
@jwt_required()
@cache.cached(timeout=3600, key_prefix=lambda: f'weekly_nutrition_{get_jwt_identity()}_{request.args.get("end_date", datetime.now().strftime("%Y-%m-%d"))}')
def get_weekly_nutrition():
    """주간 영양 섭취 분석 API"""
    current_user_id = get_jwt_identity()

    # 종료 날짜 (기본: 오늘)
    end_date_str = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))

    try:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        start_date = end_date - timedelta(days=6)  # 7일간의 데이터
    except ValueError:
        return error_response('날짜 형식이 올바르지 않습니다.', 400)

    # 날짜별 영양 정보 초기화
    daily_nutrition = {}
    for i in range(7):
        current_date = start_date + timedelta(days=i)
        daily_nutrition[current_date.strftime('%Y-%m-%d')] = {
            'date': current_date.strftime('%Y-%m-%d'),
            'nutrition': {},
            'meal_count': 0
        }

    # 해당 기간의 식사 조회
    meals = Meal.query.filter(
        Meal.uid == current_user_id,
        Meal.date >= start_date,
        Meal.date <= end_date
    ).all()

    # 날짜별 식사 분류 및 영양 분석
    for meal in meals:
        date_str = meal.date.strftime('%Y-%m-%d')
        daily_nutrition[date_str]['meal_count'] += 1

        foods = Food.query.filter_by(mid=meal.mid).all()
        food_names = [food.food_name for food in foods]

        if food_names:
            try:
                nutrition = analyze_meal_nutrition(food_names)

                # 기존 영양 정보에 합산
                if not daily_nutrition[date_str]['nutrition']:
                    daily_nutrition[date_str]['nutrition'] = nutrition
                else:
                    for key, value in nutrition.items():
                        if key in daily_nutrition[date_str]['nutrition']:
                            daily_nutrition[date_str]['nutrition'][key] += value
                        else:
                            daily_nutrition[date_str]['nutrition'][key] = value
            except Exception as e:
                current_app.logger.error(f"영양 분석 오류: {str(e)}")

    # 주간 평균 계산
    weekly_average = {}
    days_with_data = 0

    for day_data in daily_nutrition.values():
        if day_data['nutrition']:
            days_with_data += 1
            for key, value in day_data['nutrition'].items():
                if key in weekly_average:
                    weekly_average[key] += value
                else:
                    weekly_average[key] = value

    if days_with_data > 0:
        for key in weekly_average:
            weekly_average[key] /= days_with_data

    # 사용자 정보
    user = User.query.filter_by(uid=current_user_id).first()

    # 주간 인사이트
    weekly_insights = get_nutrition_insights(weekly_average, user, is_average=True)

    return success_response({
        'period': {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        },
        'daily_nutrition': list(daily_nutrition.values()),
        'weekly_average': weekly_average,
        'insights': weekly_insights,
        'total_meals': sum(day['meal_count'] for day in daily_nutrition.values())
    })

@nutrition_bp.route('/research', methods=['GET'])
@jwt_required()
def get_nutrition_research():
    """영양 관련 연구 정보 API (RAG 활용)"""
    query = request.args.get('query', '')

    if not query:
        return error_response('검색어가 필요합니다.', 400)

    try:
        # RAG 서비스를 통한 영양 연구 정보 검색
        research_data = get_nutritional_research(query)

        return success_response({
            'query': query,
            'results': research_data
        })
    except Exception as e:
        current_app.logger.error(f"연구 정보 검색 오류: {str(e)}")
        return error_response(f'연구 정보 검색 실패: {str(e)}', 500)