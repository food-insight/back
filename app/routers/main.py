from flask import Blueprint, jsonify, current_app, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.extensions import db, cache
from models.user import User
from models.meal import Meal
from models.food import Food
from models.recommendation import Recommendation
from utils.responses import success_response, error_response
from datetime import datetime, timedelta

main_bp = Blueprint('main', __name__)

@main_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@cache.cached(timeout=300, key_prefix=lambda: f'dashboard_{get_jwt_identity()}')
def get_dashboard():
    """메인 대시보드 API"""
    current_user_id = get_jwt_identity()

    # 사용자 정보
    user = User.query.filter_by(uid=current_user_id).first()
    if not user:
        return error_response('사용자를 찾을 수 없습니다.', 404)

    # 오늘 날짜
    today = datetime.now().date()

    # 오늘의 식사 목록
    today_meals = Meal.query.filter_by(
        uid=current_user_id,
        date=today
    ).order_by(Meal.mid.desc()).all()

    # 오늘의 영양 섭취 정보
    today_nutrition = {}
    if today_meals:
        all_foods = []
        for meal in today_meals:
            foods = Food.query.filter_by(mid=meal.mid).all()
            for food in foods:
                all_foods.append(food.food_name)

        if all_foods:
            from services.nutrition_analysis import analyze_meal_nutrition
            try:
                today_nutrition = analyze_meal_nutrition(all_foods)
            except Exception as e:
                current_app.logger.error(f"영양 분석 오류: {str(e)}")

    # 최근 추천 정보
    recent_recommendations = Recommendation.query.filter_by(
        uid=current_user_id
    ).order_by(Recommendation.rid.desc()).limit(3).all()

    # 목표 달성 상태
    goal_status = {
        'calories': {
            'current': today_nutrition.get('calories', 0),
            'target': 2000,  # 사용자 정보에 따라 조정 가능
            'percentage': min(100, round(today_nutrition.get('calories', 0) / 2000 * 100, 1))
        },
        'protein': {
            'current': today_nutrition.get('protein', 0),
            'target': 60,  # 사용자 정보에 따라 조정 가능
            'percentage': min(100, round(today_nutrition.get('protein', 0) / 60 * 100, 1))
        },
        'water': {
            'current': 1200,  # 실제로는 사용자 입력 또는 다른 소스에서 가져와야 함
            'target': 2000,
            'percentage': 60
        }
    }

    return success_response({
        'user': user.to_dict(),
        'today_date': today.strftime('%Y-%m-%d'),
        'today_meals': [meal.to_dict() for meal in today_meals],
        'today_nutrition': today_nutrition,
        'goal_status': goal_status,
        'recent_recommendations': [rec.to_dict() for rec in recent_recommendations]
    })

@main_bp.route('/quick-stats', methods=['GET'])
@jwt_required()
def get_quick_stats():
    """빠른 통계 정보 API"""
    current_user_id = get_jwt_identity()

    # 오늘 날짜
    today = datetime.now().date()

    # 최근 7일 기간
    week_start = today - timedelta(days=6)

    # 오늘 기록된 식사 수
    today_meal_count = Meal.query.filter_by(
        uid=current_user_id,
        date=today
    ).count()

    # 주간 식사 기록 수
    weekly_meal_count = Meal.query.filter(
        Meal.uid == current_user_id,
        Meal.date >= week_start,
        Meal.date <= today
    ).count()

    # 최근 기록된 식사
    last_meal = Meal.query.filter_by(
        uid=current_user_id
    ).order_by(Meal.date.desc(), Meal.mid.desc()).first()

    # 최근 추천
    last_recommendation = Recommendation.query.filter_by(
        uid=current_user_id
    ).order_by(Recommendation.rid.desc()).first()

    return success_response({
        'today_meal_count': today_meal_count,
        'weekly_meal_count': weekly_meal_count,
        'last_meal': last_meal.to_dict() if last_meal else None,
        'last_recommendation': last_recommendation.to_dict() if last_recommendation else None,
        'today_date': today.strftime('%Y-%m-%d'),
        'week_start_date': week_start.strftime('%Y-%m-%d')
    })

@main_bp.route('/featured-content', methods=['GET'])
def get_featured_content():
    """추천 컨텐츠 API"""
    # 캐시 설정 (1시간)
    cached_data = cache.get('featured_content')
    if cached_data:
        return success_response(cached_data)

    # 추천 건강 팁 목록
    health_tips = [
        {
            'id': 1,
            'title': '균형 잡힌 식단의 중요성',
            'content': '균형 잡힌 식단은 다양한 영양소를 섭취하는 것이 중요합니다. 단백질, 탄수화물, 지방, 비타민, 미네랄을 적절히 포함시키세요.',
            'image_url': '/static/images/balanced-diet.jpg'
        },
        {
            'id': 2,
            'title': '물 마시는 습관',
            'content': '하루에 최소 2리터의 물을 마시는 것이 좋습니다. 충분한 수분 섭취는 대사와 소화에 도움을 줍니다.',
            'image_url': '/static/images/water-intake.jpg'
        },
        {
            'id': 3,
            'title': '식이 섬유의 중요성',
            'content': '식이 섬유는 소화를 돕고 포만감을 유지하는 데 중요합니다. 과일, 채소, 통곡물에 풍부하게 포함되어 있습니다.',
            'image_url': '/static/images/fiber-foods.jpg'
        }
    ]

    # 추천 레시피
    featured_recipes = [
        {
            'id': 1,
            'title': '아보카도 토스트',
            'description': '건강한 지방과 단백질이 풍부한 간단한 아침 식사',
            'image_url': '/static/images/avocado-toast.jpg',
            'calories': 320,
            'protein': 12
        },
        {
            'id': 2,
            'title': '퀴노아 샐러드',
            'description': '단백질과 식이 섬유가 풍부한 가벼운 점심 메뉴',
            'image_url': '/static/images/quinoa-salad.jpg',
            'calories': 380,
            'protein': 14
        },
        {
            'id': 3,
            'title': '그릴드 치킨 샐러드',
            'description': '저칼로리 고단백 저녁 식사',
            'image_url': '/static/images/grilled-chicken.jpg',
            'calories': 420,
            'protein': 35
        }
    ]

    # 공지사항
    announcements = [
        {
            'id': 1,
            'title': '앱 업데이트 안내',
            'content': '최신 버전이 출시되었습니다. 더 정확한 영양 분석과 개선된 UI를 만나보세요.',
            'date': '2025-03-01'
        },
        {
            'id': 2,
            'title': '새로운 기능: 음성 인식',
            'content': '이제 음성으로 식사를 기록할 수 있습니다. 직접 말해보세요!',
            'date': '2025-02-15'
        }
    ]

    response_data = {
        'health_tips': health_tips,
        'featured_recipes': featured_recipes,
        'announcements': announcements
    }

    # 캐시에 저장
    cache.set('featured_content', response_data, timeout=3600)  # 1시간

    return success_response(response_data)

@main_bp.route('/search', methods=['GET'])
@jwt_required()
def search():
    """통합 검색 API"""
    query = request.args.get('q', '')

    if not query or len(query) < 2:
        return error_response('검색어는 2글자 이상이어야 합니다.', 400)

    current_user_id = get_jwt_identity()
    search_results = {}

    # 식사 기록 검색
    meals = Meal.query.filter(
        Meal.uid == current_user_id,
        Meal.content.like(f'%{query}%')
    ).order_by(Meal.date.desc()).limit(5).all()

    # 음식 검색
    foods = Food.query.join(Meal).filter(
        Meal.uid == current_user_id,
        Food.food_name.like(f'%{query}%')
    ).order_by(Food.fid.desc()).limit(5).all()

    # 레시피 검색 (외부 서비스 활용)
    from services.recommendation import search_recipes
    try:
        recipes = search_recipes(query)
    except Exception as e:
        current_app.logger.error(f"레시피 검색 오류: {str(e)}")
        recipes = []

    search_results = {
        'query': query,
        'meals': [meal.to_dict() for meal in meals],
        'foods': [{'fid': food.fid, 'food_name': food.food_name, 'meal_id': food.mid} for food in foods],
        'recipes': recipes
    }

    return success_response(search_results)