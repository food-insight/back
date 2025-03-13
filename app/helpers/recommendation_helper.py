from flask import current_app
from datetime import datetime, timedelta
from models.meal import Meal
from models.food import Food
from models.allergy import Allergy
from models.user import User
from app.extensions import db
from collections import Counter

def get_user_dietary_preferences(user_id):
    """사용자 식이 선호도 추출 헬퍼 함수"""
    # 사용자 정보
    user = User.query.filter_by(uid=user_id).first()
    if not user:
        return {}, []

    # 알레르기 정보
    allergies = Allergy.query.filter_by(uid=user_id).all()
    allergy_list = [allergy.allergy_name for allergy in allergies]

    # 최근 3개월간의 식사 기록
    three_months_ago = datetime.now().date() - timedelta(days=90)
    meals = Meal.query.filter(
        Meal.uid == user_id,
        Meal.date >= three_months_ago
    ).all()

    # 음식 빈도 분석
    food_frequency = Counter()
    meal_time_preference = Counter()
    category_preference = Counter()

    for meal in meals:
        meal_time_preference[meal.meal_time] += 1

        foods = Food.query.filter_by(mid=meal.mid).all()
        for food in foods:
            food_frequency[food.food_name] += 1
            if food.category:
                category_preference[food.category] += 1

    # 건강 목표
    health_goal = user.health_goal

    preferences = {
        'favorite_foods': food_frequency.most_common(10),
        'meal_time_preference': meal_time_preference,
        'category_preference': category_preference.most_common(5),
        'health_goal': health_goal
    }

    return preferences, allergy_list

def filter_recommendations_by_allergies(recommendations, allergies):
    """알레르기 정보를 기반으로 추천 필터링 헬퍼 함수"""
    if not allergies:
        return recommendations

    filtered_recommendations = []

    for rec in recommendations:
        # 알레르기 항목 포함 여부 확인
        is_safe = True
        food_name = rec.get('name', '').lower()

        for allergy in allergies:
            if allergy.lower() in food_name:
                is_safe = False
                break

        # 안전한 음식만 포함
        if is_safe:
            filtered_recommendations.append(rec)

    return filtered_recommendations

def personalize_recommendations(recommendations, user):
    """사용자 맞춤형 추천 조정 헬퍼 함수"""
    if not recommendations or not user:
        return recommendations

    personalized_recs = recommendations.copy()

    # 건강 목표에 따른 조정
    health_goal = user.health_goal or ''

    if '체중 감량' in health_goal or '다이어트' in health_goal:
        # 저칼로리 음식 우선 정렬
        personalized_recs.sort(key=lambda x: x.get('calories', 1000))
    elif '근육 증가' in health_goal or '벌크업' in health_goal:
        # 고단백 음식 우선 정렬
        personalized_recs.sort(key=lambda x: x.get('protein', 0), reverse=True)
    elif '당뇨' in health_goal:
        # 저탄수화물 음식 우선 정렬
        personalized_recs.sort(key=lambda x: x.get('carbs', 100))
    elif '고혈압' in health_goal:
        # 저나트륨 음식 우선 정렬
        personalized_recs.sort(key=lambda x: x.get('sodium', 1000))

    return personalized_recs

def generate_recipe_recommendation_reasons(recipe, user_preferences):
    """레시피 추천 이유 생성 헬퍼 함수"""
    if not recipe or not user_preferences:
        return "맞춤형 추천"

    reasons = []

    # 건강 목표 기반 이유
    health_goal = user_preferences.get('health_goal', '')
    if health_goal:
        if '체중 감량' in health_goal and recipe.get('calories', 1000) < 500:
            reasons.append(f"저칼로리({recipe.get('calories')}kcal) 식단에 적합")
        elif '근육 증가' in health_goal and recipe.get('protein', 0) > 25:
            reasons.append(f"고단백({recipe.get('protein')}g) 식단에 적합")
        elif '당뇨' in health_goal and recipe.get('carbs', 100) < 30:
            reasons.append(f"저탄수화물({recipe.get('carbs')}g) 식단에 적합")
        elif '고혈압' in health_goal and recipe.get('sodium', 1000) < 500:
            reasons.append(f"저나트륨({recipe.get('sodium')}mg) 식단에 적합")

    # 선호 카테고리 기반 이유
    favorite_categories = [cat for cat, _ in user_preferences.get('category_preference', [])]
    if recipe.get('category') in favorite_categories:
        reasons.append(f"선호하는 카테고리({recipe.get('category')})에 속함")

    # 이유가 없으면 기본 이유
    if not reasons:
        reasons.append("영양 균형이 좋은 식단")

    return ", ".join(reasons)

def calculate_similarity_score(food_name, user_preferences):
    """음식과 사용자 선호도 유사성 점수 계산 헬퍼 함수"""
    if not food_name or not user_preferences:
        return 0

    score = 0
    food_name_lower = food_name.lower()

    # 선호 음식과의 유사성
    favorite_foods = [food.lower() for food, _ in user_preferences.get('favorite_foods', [])]
    for fav_food in favorite_foods:
        if fav_food in food_name_lower or food_name_lower in fav_food:
            score += 10
            break

    # 선호 카테고리와의 유사성
    favorite_categories = [cat.lower() for cat, _ in user_preferences.get('category_preference', [])]
    for category in favorite_categories:
        if category in food_name_lower:
            score += 5
            break

    return score

def format_recommendation_data(recommendations, reasons=None):
    """추천 데이터 포맷팅 헬퍼 함수"""
    if not recommendations:
        return []

    formatted_data = []

    for i, rec in enumerate(recommendations):
        item = rec.copy()

        # 이유 추가
        reason = reasons[i] if reasons and i < len(reasons) else "맞춤형 추천"
        item['reason'] = reason

        # 필요한 경우 영양 정보 형식 조정
        if 'nutrition' in item and isinstance(item['nutrition'], dict):
            formatted_nutrition = {}
            for key, value in item['nutrition'].items():
                if isinstance(value, (int, float)):
                    formatted_nutrition[key] = round(value, 1)
                else:
                    formatted_nutrition[key] = value
            item['nutrition'] = formatted_nutrition

        formatted_data.append(item)

    return formatted_data