from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db, cache
from models.meal import Meal
from models.food import Food
from models.user import User
from models.recommendation import Recommendation
from models.allergy import Allergy
from services.recommendation import generate_meal_recommendations, generate_food_alternatives
from services.rag_service import get_recipe_recommendations
from utils.response import success_response, error_response
from datetime import datetime, timedelta

recommendation_bp = Blueprint('recommendation', __name__)

@recommendation_bp.route('/meal', methods=['GET'])
@jwt_required()
@cache.cached(timeout=3600, key_prefix=lambda: f'meal_recommendations_{get_jwt_identity()}')
def get_meal_recommendations():
    """개인 맞춤형 식단 추천 API"""
    current_user_id = get_jwt_identity()

    # 사용자 정보 조회
    user = User.query.filter_by(uid=current_user_id).first()
    if not user:
        return error_response('사용자 정보를 찾을 수 없습니다.', 404)

    # 사용자 알레르기 정보
    allergies = Allergy.query.filter_by(uid=current_user_id).all()
    allergy_list = [allergy.allergy_name for allergy in allergies]

    # 최근 식사 기록 조회 (지난 30일)
    start_date = datetime.now().date() - timedelta(days=30)
    recent_meals = Meal.query.filter(
        Meal.uid == current_user_id,
        Meal.date >= start_date
    ).all()

    # 최근 먹은 음식 목록
    recent_foods = []
    for meal in recent_meals:
        foods = Food.query.filter_by(mid=meal.mid).all()
        for food in foods:
            recent_foods.append(food.food_name)

    try:
        # 맞춤형 식단 추천 생성
        recommendations = generate_meal_recommendations(
            user=user,
            allergies=allergy_list,
            recent_foods=recent_foods
        )

        # DB에 추천 정보 저장
        for rec_type, rec_items in recommendations.items():
            for item in rec_items:
                recommendation = Recommendation(
                    uid=current_user_id,
                    reason=f"{rec_type} 기반 추천: {item['reason'] if 'reason' in item else ''}"
                )
                db.session.add(recommendation)

        db.session.commit()

        return success_response({
            'recommendations': recommendations,
            'user_allergies': allergy_list,
            'health_goal': user.health_goal
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"식단 추천 오류: {str(e)}")
        return error_response(f'식단 추천 생성 실패: {str(e)}', 500)

@recommendation_bp.route('/alternatives', methods=['POST'])
@jwt_required()
def get_food_alternatives():
    """음식 대체 추천 API"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    # 필수 필드 확인
    if 'food_name' not in data:
        return error_response('food_name 필드가 필요합니다.', 400)

    food_name = data['food_name']
    reason = data.get('reason', '건강한 대체 음식')  # 대체 이유 (칼로리 감소, 단백질 증가 등)

    # 사용자 알레르기 정보
    allergies = Allergy.query.filter_by(uid=current_user_id).all()
    allergy_list = [allergy.allergy_name for allergy in allergies]

    try:
        # 대체 음식 추천
        alternatives = generate_food_alternatives(
            food_name=food_name,
            reason=reason,
            allergies=allergy_list
        )

        # DB에 추천 정보 저장
        for alt in alternatives:
            recommendation = Recommendation(
                uid=current_user_id,
                reason=f"{food_name}의 대체 음식 ({reason}): {alt['name']}"
            )
            db.session.add(recommendation)

        db.session.commit()

        return success_response({
            'original_food': food_name,
            'reason': reason,
            'alternatives': alternatives
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"대체 음식 추천 오류: {str(e)}")
        return error_response(f'대체 음식 추천 실패: {str(e)}', 500)

@recommendation_bp.route('/recipes', methods=['GET'])
@jwt_required()
def get_recipes():
    """레시피 추천 API"""
    current_user_id = get_jwt_identity()

    # 쿼리 파라미터
    ingredients = request.args.get('ingredients', '')
    meal_type = request.args.get('meal_type', '')
    health_goal = request.args.get('health_goal', '')

    # 사용자 건강 목표가 지정되지 않았으면 사용자 프로필에서 가져오기
    if not health_goal:
        user = User.query.filter_by(uid=current_user_id).first()
        if user and user.health_goal:
            health_goal = user.health_goal

    # 사용자 알레르기 정보
    allergies = Allergy.query.filter_by(uid=current_user_id).all()
    allergy_list = [allergy.allergy_name for allergy in allergies]

    try:
        # RAG 서비스를 통한 레시피 추천
        recipes = get_recipe_recommendations(
            ingredients=ingredients.split(',') if ingredients else [],
            meal_type=meal_type,
            health_goal=health_goal,
            allergies=allergy_list
        )

        return success_response({
            'ingredients': ingredients,
            'meal_type': meal_type,
            'health_goal': health_goal,
            'recipes': recipes
        })
    except Exception as e:
        current_app.logger.error(f"레시피 추천 오류: {str(e)}")
        return error_response(f'레시피 추천 실패: {str(e)}', 500)

@recommendation_bp.route('/history', methods=['GET'])
@jwt_required()
def get_recommendation_history():
    """추천 히스토리 API"""
    current_user_id = get_jwt_identity()

    # 페이지네이션
    limit = int(request.args.get('limit', 10))
    page = int(request.args.get('page', 1))

    # 추천 기록 조회
    query = Recommendation.query.filter_by(uid=current_user_id)
    total_count = query.count()
    total_pages = (total_count + limit - 1) // limit

    recommendations = query.order_by(Recommendation.rid.desc()) \
        .offset((page - 1) * limit) \
        .limit(limit) \
        .all()

    return success_response({
        'recommendations': [rec.to_dict() for rec in recommendations],
        'pagination': {
            'total_count': total_count,
            'total_pages': total_pages,
            'current_page': page,
            'limit': limit
        }
    })