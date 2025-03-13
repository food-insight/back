import logging
from typing import List, Dict, Any, Optional, Tuple
from flask import current_app
from models.user import User
from services.nutrition_analysis import analyze_meal_nutrition, get_food_nutrition

# 로깅 설정
logger = logging.getLogger(__name__)

# 샘플 음식 데이터베이스 (실제 구현에서는 DB에서 조회)
FOOD_DB = [
    {"name": "김치찌개", "category": "국/찌개", "calories": 250, "protein": 15, "fat": 12, "carbs": 10, "tags": ["Korean", "spicy", "hot"]},
    {"name": "된장찌개", "category": "국/찌개", "calories": 200, "protein": 12, "fat": 10, "carbs": 8, "tags": ["Korean", "savory"]},
    {"name": "순두부찌개", "category": "국/찌개", "calories": 220, "protein": 14, "fat": 11, "carbs": 9, "tags": ["Korean", "spicy", "tofu"]},
    {"name": "불고기", "category": "육류", "calories": 400, "protein": 30, "fat": 25, "carbs": 10, "tags": ["Korean", "beef", "grilled"]},
    {"name": "삼겹살", "category": "육류", "calories": 500, "protein": 25, "fat": 42, "carbs": 0, "tags": ["Korean", "pork", "grilled"]},
    {"name": "닭갈비", "category": "육류", "calories": 350, "protein": 28, "fat": 20, "carbs": 12, "tags": ["Korean", "chicken", "spicy"]},
    {"name": "비빔밥", "category": "밥류", "calories": 600, "protein": 20, "fat": 15, "carbs": 80, "tags": ["Korean", "rice", "mixed"]},
    {"name": "제육볶음", "category": "육류", "calories": 450, "protein": 30, "fat": 28, "carbs": 15, "tags": ["Korean", "pork", "spicy"]},
    {"name": "김밥", "category": "분식", "calories": 350, "protein": 10, "fat": 8, "carbs": 65, "tags": ["Korean", "rice", "seaweed"]},
    {"name": "떡볶이", "category": "분식", "calories": 450, "protein": 8, "fat": 12, "carbs": 80, "tags": ["Korean", "spicy", "rice cake"]},
    {"name": "라면", "category": "면류", "calories": 500, "protein": 10, "fat": 20, "carbs": 70, "tags": ["Korean", "noodle", "instant"]},
    {"name": "잡채", "category": "반찬", "calories": 320, "protein": 10, "fat": 15, "carbs": 45, "tags": ["Korean", "noodle", "vegetables"]},
    {"name": "돈까스", "category": "육류", "calories": 550, "protein": 25, "fat": 35, "carbs": 40, "tags": ["Japanese", "pork", "fried"]},
    {"name": "치킨", "category": "육류", "calories": 450, "protein": 35, "fat": 30, "carbs": 15, "tags": ["chicken", "fried"]},
    {"name": "냉면", "category": "면류", "calories": 480, "protein": 15, "fat": 5, "carbs": 85, "tags": ["Korean", "noodle", "cold"]},
    {"name": "쌀밥", "category": "주식", "calories": 300, "protein": 5, "fat": 0.5, "carbs": 65, "tags": ["rice", "basic"]},
    {"name": "현미밥", "category": "주식", "calories": 280, "protein": 6, "fat": 1, "carbs": 60, "tags": ["rice", "healthy", "brown rice"]},
    {"name": "두부조림", "category": "반찬", "calories": 150, "protein": 10, "fat": 8, "carbs": 5, "tags": ["Korean", "tofu", "healthy"]},
    {"name": "시금치나물", "category": "반찬", "calories": 80, "protein": 3, "fat": 4, "carbs": 8, "tags": ["Korean", "vegetables", "healthy"]},
    {"name": "계란말이", "category": "반찬", "calories": 150, "protein": 12, "fat": 10, "carbs": 2, "tags": ["Korean", "egg"]},
    {"name": "닭가슴살 샐러드", "category": "샐러드", "calories": 200, "protein": 30, "fat": 5, "carbs": 10, "tags": ["healthy", "chicken", "diet"]},
    {"name": "연어 스테이크", "category": "육류", "calories": 300, "protein": 35, "fat": 15, "carbs": 0, "tags": ["fish", "healthy", "omega-3"]},
    {"name": "콩나물국", "category": "국/찌개", "calories": 100, "protein": 5, "fat": 2, "carbs": 15, "tags": ["Korean", "soup", "light"]},
    {"name": "미역국", "category": "국/찌개", "calories": 120, "protein": 6, "fat": 3, "carbs": 18, "tags": ["Korean", "soup", "seaweed"]},
    {"name": "샐러드", "category": "샐러드", "calories": 100, "protein": 3, "fat": 5, "carbs": 10, "tags": ["vegetables", "healthy", "diet"]},
    {"name": "그릭 요거트", "category": "유제품", "calories": 150, "protein": 15, "fat": 8, "carbs": 5, "tags": ["dairy", "healthy", "protein"]},
    {"name": "과일 샐러드", "category": "과일", "calories": 120, "protein": 1, "fat": 0, "carbs": 30, "tags": ["fruit", "healthy", "sweet"]},
    {"name": "견과류 믹스", "category": "간식", "calories": 250, "protein": 8, "fat": 20, "carbs": 10, "tags": ["nuts", "healthy", "snack"]},
]

# 샘플 레시피 데이터베이스
RECIPE_DB = [
    {
        "title": "건강한 비빔밥",
        "ingredients": ["현미밥", "시금치나물", "콩나물", "당근", "소고기", "계란", "참기름", "고추장"],
        "instructions": "1. 현미밥을 그릇에 담습니다.\n2. 준비된 나물과 고기를 올립니다.\n3. 계란 프라이를 올립니다.\n4. 고추장과 참기름을 넣고 비벼 먹습니다.",
        "calories": 550,
        "protein": 25,
        "fat": 15,
        "carbs": 70,
        "time": 25,
        "difficulty": "쉬움",
        "tags": ["Korean", "healthy", "balanced"],
        "health_goals": ["체중 관리", "근육 증가"]
    },
    {
        "title": "저탄수화물 닭가슴살 샐러드",
        "ingredients": ["닭가슴살", "로메인 상추", "방울토마토", "오이", "올리브 오일", "레몬즙", "소금", "후추"],
        "instructions": "1. 닭가슴살을 익혀 썰어둡니다.\n2. 채소를 씻어 먹기 좋게 썹니다.\n3. 올리브 오일, 레몬즙, 소금, 후추로 드레싱을 만듭니다.\n4. 모든 재료를 섞어 드레싱과 함께 즐깁니다.",
        "calories": 250,
        "protein": 35,
        "fat": 10,
        "carbs": 5,
        "time": 20,
        "difficulty": "쉬움",
        "tags": ["low-carb", "high-protein", "salad"],
        "health_goals": ["체중 감량", "다이어트"]
    },
    {
        "title": "두부 스크램블",
        "ingredients": ["두부", "양파", "피망", "당근", "강황", "소금", "후추", "올리브 오일"],
        "instructions": "1. 두부를 으깨서 물기를 제거합니다.\n2. 야채를 잘게 썹니다.\n3. 올리브 오일을 두른 팬에 야채를 볶다가 두부를 넣습니다.\n4. 강황, 소금, 후추를 넣고 계란 스크램블처럼 볶아줍니다.",
        "calories": 180,
        "protein": 15,
        "fat": 10,
        "carbs": 8,
        "time": 15,
        "difficulty": "쉬움",
        "tags": ["vegetarian", "breakfast", "high-protein"],
        "health_goals": ["체중 감량", "채식"]
    },
    {
        "title": "프로틴 그릭요거트 볼",
        "ingredients": ["그릭 요거트", "프로틴 파우더", "블루베리", "바나나", "그래놀라", "꿀"],
        "instructions": "1. 그릭 요거트에 프로틴 파우더를 섞습니다.\n2. 그릇에 요거트를 담고 과일과 그래놀라를 올립니다.\n3. 꿀을 살짝 뿌려 마무리합니다.",
        "calories": 350,
        "protein": 30,
        "fat": 10,
        "carbs": 40,
        "time": 10,
        "difficulty": "쉬움",
        "tags": ["breakfast", "high-protein", "quick"],
        "health_goals": ["근육 증가", "아침 식사"]
    },
    {
        "title": "연어 아보카도 샐러드",
        "ingredients": ["훈제 연어", "아보카도", "상추", "토마토", "적양파", "올리브 오일", "레몬즙", "딜"],
        "instructions": "1. 모든 채소를 썰어 그릇에 담습니다.\n2. 연어와 아보카도를 올립니다.\n3. 올리브 오일, 레몬즙, 딜로 드레싱을 만들어 뿌립니다.",
        "calories": 320,
        "protein": 25,
        "fat": 22,
        "carbs": 8,
        "time": 15,
        "difficulty": "쉬움",
        "tags": ["low-carb", "omega-3", "salad"],
        "health_goals": ["체중 관리", "심장 건강"]
    }
]

def generate_meal_recommendations(user: Optional[User], allergies: List[str] = [], recent_foods: List[str] = []) -> Dict[str, List[Dict[str, Any]]]:
    """
    사용자 맞춤형 식단 추천 생성

    Args:
        user (Optional[User]): 사용자 정보
        allergies (List[str]): 알레르기 정보
        recent_foods (List[str]): 최근 먹은 음식 목록

    Returns:
        Dict[str, List[Dict[str, Any]]]: 카테고리별 추천 목록
    """
    try:
        logger.info("식단 추천 생성 시작")

        recommendations = {
            "health_based": [],  # 건강 목표 기반 추천
            "balanced_meal": [],  # 균형 잡힌 식단 추천
            "variety_based": []   # 다양성 기반 추천 (최근에 먹지 않은 음식)
        }

        # 알레르기 필터링 함수
        def is_safe_for_allergies(food):
            for allergy in allergies:
                if allergy.lower() in food["name"].lower():
                    return False
                # 태그에서도 알레르기 체크 (예: 땅콩 알레르기 -> "nuts" 태그 체크)
                for tag in food.get("tags", []):
                    if allergy.lower() in tag.lower():
                        return False
            return True

        # 알레르기 필터링
        safe_foods = [food for food in FOOD_DB if is_safe_for_allergies(food)]

        if not safe_foods:
            logger.warning("알레르기를 고려한 안전한 음식이 없습니다.")
            return recommendations

        # 1. 건강 목표 기반 추천
        if user and user.health_goal:
            health_goal = user.health_goal.lower()

            if "체중 감량" in health_goal or "다이어트" in health_goal:
                # 저칼로리, 고단백 음식 추천
                diet_foods = sorted([f for f in safe_foods if f["calories"] < 300 and f["protein"] > 15],
                                    key=lambda x: x["calories"])

                for food in diet_foods[:3]:
                    recommendations["health_based"].append({
                        "name": food["name"],
                        "category": food["category"],
                        "reason": "저칼로리 고단백 식품으로 다이어트에 적합합니다.",
                        "nutrition": {
                            "calories": food["calories"],
                            "protein": food["protein"],
                            "fat": food["fat"],
                            "carbs": food["carbs"]
                        }
                    })

            elif "근육 증가" in health_goal or "벌크업" in health_goal:
                # 고단백, 고칼로리 음식 추천
                protein_foods = sorted([f for f in safe_foods if f["protein"] > 20],
                                       key=lambda x: x["protein"], reverse=True)

                for food in protein_foods[:3]:
                    recommendations["health_based"].append({
                        "name": food["name"],
                        "category": food["category"],
                        "reason": "고단백 식품으로 근육 성장에 도움이 됩니다.",
                        "nutrition": {
                            "calories": food["calories"],
                            "protein": food["protein"],
                            "fat": food["fat"],
                            "carbs": food["carbs"]
                        }
                    })

            elif "당뇨" in health_goal:
                # 저탄수화물 음식 추천
                low_carb_foods = sorted([f for f in safe_foods if f["carbs"] < 15],
                                        key=lambda x: x["carbs"])

                for food in low_carb_foods[:3]:
                    recommendations["health_based"].append({
                        "name": food["name"],
                        "category": food["category"],
                        "reason": "저탄수화물 식품으로 혈당 관리에 도움이 됩니다.",
                        "nutrition": {
                            "calories": food["calories"],
                            "protein": food["protein"],
                            "fat": food["fat"],
                            "carbs": food["carbs"]
                        }
                    })

            elif "고혈압" in health_goal:
                # 저나트륨 음식 추천 (여기서는 간단히 몇 가지 음식 선정)
                low_sodium_foods = ["두부조림", "시금치나물", "콩나물국", "닭가슴살 샐러드", "과일 샐러드"]

                for food_name in low_sodium_foods:
                    food = next((f for f in safe_foods if f["name"] == food_name), None)
                    if food:
                        recommendations["health_based"].append({
                            "name": food["name"],
                            "category": food["category"],
                            "reason": "저나트륨 식품으로 혈압 관리에 도움이 됩니다.",
                            "nutrition": {
                                "calories": food["calories"],
                                "protein": food["protein"],
                                "fat": food["fat"],
                                "carbs": food["carbs"]
                            }
                        })

            # 추천이 3개 미만이면 일반적인 건강식 추가
            if len(recommendations["health_based"]) < 3:
                healthy_foods = [f for f in safe_foods if "healthy" in f.get("tags", [])]
                for food in healthy_foods[:3 - len(recommendations["health_based"])]:
                    recommendations["health_based"].append({
                        "name": food["name"],
                        "category": food["category"],
                        "reason": "전반적인 건강에 좋은 식품입니다.",
                        "nutrition": {
                            "calories": food["calories"],
                            "protein": food["protein"],
                            "fat": food["fat"],
                            "carbs": food["carbs"]
                        }
                    })

        # 2. 균형 잡힌 식단 추천 (주식 + 반찬 + 국/찌개)
        main_dishes = [f for f in safe_foods if f["category"] in ["주식", "밥류"]]
        side_dishes = [f for f in safe_foods if f["category"] in ["반찬", "육류"]]
        soups = [f for f in safe_foods if f["category"] in ["국/찌개"]]

        import random

        # 식사 조합 생성 (최대 3개)
        for _ in range(min(3, min(len(main_dishes), len(side_dishes), len(soups)))):
            main = random.choice(main_dishes)
            side = random.choice(side_dishes)
            soup = random.choice(soups)

            # 중복 제거
            main_dishes.remove(main)
            side_dishes.remove(side)
            soups.remove(soup)

            meal_combo = {
                "name": f"{main['name']} + {side['name']} + {soup['name']}",
                "components": [
                    {"name": main["name"], "category": main["category"]},
                    {"name": side["name"], "category": side["category"]},
                    {"name": soup["name"], "category": soup["category"]}
                ],
                "reason": "영양 균형이 잘 맞는 한식 식단입니다.",
                "nutrition": {
                    "calories": main["calories"] + side["calories"] + soup["calories"],
                    "protein": main["protein"] + side["protein"] + soup["protein"],
                    "fat": main["fat"] + side["fat"] + soup["fat"],
                    "carbs": main["carbs"] + side["carbs"] + soup["carbs"]
                }
            }

            recommendations["balanced_meal"].append(meal_combo)

        # 3. 다양성 기반 추천 (최근에 먹지 않은 음식)
        recent_food_set = set(recent_foods)
        not_recent_foods = [f for f in safe_foods if f["name"] not in recent_food_set]

        # 랜덤하게 3개 선택
        selected_foods = random.sample(not_recent_foods, min(3, len(not_recent_foods)))

        for food in selected_foods:
            recommendations["variety_based"].append({
                "name": food["name"],
                "category": food["category"],
                "reason": "최근에 드시지 않은 음식으로, 식단의 다양성을 높여줍니다.",
                "nutrition": {
                    "calories": food["calories"],
                    "protein": food["protein"],
                    "fat": food["fat"],
                    "carbs": food["carbs"]
                }
            })

        logger.info(f"식단 추천 생성 완료: {sum(len(recs) for recs in recommendations.values())}개 추천")
        return recommendations

    except Exception as e:
        logger.error(f"식단 추천 생성 중 오류 발생: {str(e)}")
        return {
            "health_based": [],
            "balanced_meal": [],
            "variety_based": []
        }

def generate_food_alternatives(food_name: str, reason: str = "건강한 대체 음식", allergies: List[str] = []) -> List[Dict[str, Any]]:
    """
    특정 음식의 대체 음식 추천

    Args:
        food_name (str): 원본 음식 이름
        reason (str): 대체 이유 (예: 칼로리 감소, 단백질 증가)
        allergies (List[str]): 알레르기 정보

    Returns:
        List[Dict[str, Any]]: 대체 음식 추천 목록
    """
    try:
        logger.info(f"음식 대체 추천 시작: {food_name}")

        # 원본 음식 찾기
        original_food = next((f for f in FOOD_DB if f["name"] == food_name), None)

        if not original_food:
            logger.warning(f"원본 음식 '{food_name}'을 찾을 수 없습니다.")
            # 임의의 음식 3개 반환
            import random
            return [{"name": f["name"], "category": f["category"], "reason": "다양한 식단을 위한 추천"}
                    for f in random.sample(FOOD_DB, min(3, len(FOOD_DB)))]

        # 알레르기 필터링
        safe_foods = []
        for food in FOOD_DB:
            if food["name"] == food_name:
                continue  # 원본 음식 제외

            is_safe = True
            for allergy in allergies:
                if allergy.lower() in food["name"].lower():
                    is_safe = False
                    break
                for tag in food.get("tags", []):
                    if allergy.lower() in tag.lower():
                        is_safe = False
                        break

            if is_safe:
                safe_foods.append(food)

        alternatives = []

        # 이유에 따른 대체 음식 추천
        if "칼로리" in reason.lower() or "다이어트" in reason.lower():
            # 같은 카테고리의 더 낮은 칼로리 음식
            similar_category = [f for f in safe_foods if f["category"] == original_food["category"]
                                and f["calories"] < original_food["calories"]]

            sorted_alternatives = sorted(similar_category, key=lambda x: x["calories"])

            for food in sorted_alternatives[:3]:
                calorie_diff = original_food["calories"] - food["calories"]
                alternatives.append({
                    "name": food["name"],
                    "category": food["category"],
                    "reason": f"칼로리가 {calorie_diff}kcal 더 낮은 대체 음식입니다.",
                    "nutrition": {
                        "calories": food["calories"],
                        "protein": food["protein"],
                        "fat": food["fat"],
                        "carbs": food["carbs"]
                    }
                })

        elif "단백질" in reason.lower() or "근육" in reason.lower():
            # 단백질이 더 많은 음식
            high_protein = [f for f in safe_foods if f["protein"] > original_food["protein"]]

            sorted_alternatives = sorted(high_protein, key=lambda x: x["protein"], reverse=True)

            for food in sorted_alternatives[:3]:
                protein_diff = food["protein"] - original_food["protein"]
                alternatives.append({
                    "name": food["name"],
                    "category": food["category"],
                    "reason": f"단백질이 {protein_diff}g 더 많은 대체 음식입니다.",
                    "nutrition": {
                        "calories": food["calories"],
                        "protein": food["protein"],
                        "fat": food["fat"],
                        "carbs": food["carbs"]
                    }
                })

        elif "탄수화물" in reason.lower() or "당뇨" in reason.lower():
            # 탄수화물이 더 적은 음식
            low_carb = [f for f in safe_foods if f["carbs"] < original_food["carbs"]]

            sorted_alternatives = sorted(low_carb, key=lambda x: x["carbs"])

            for food in sorted_alternatives[:3]:
                carb_diff = original_food["carbs"] - food["carbs"]
                alternatives.append({
                    "name": food["name"],
                    "category": food["category"],
                    "reason": f"탄수화물이 {carb_diff}g 더 적은 대체 음식입니다.",
                    "nutrition": {
                        "calories": food["calories"],
                        "protein": food["protein"],
                        "fat": food["fat"],
                        "carbs": food["carbs"]
                    }
                })

        else:
            # 기본적으로 유사한 카테고리의 더 건강한 대안
            import random

            # 같은 카테고리 음식 중에서 "healthy" 태그가 있는 음식
            healthy_alternatives = [f for f in safe_foods if f["category"] == original_food["category"]
                                    and "healthy" in f.get("tags", [])]

            # 건강한 대안이 충분하지 않으면 같은 카테고리의 다른 음식 추가
            if len(healthy_alternatives) < 3:
                same_category = [f for f in safe_foods if f["category"] == original_food["category"]
                                 and f not in healthy_alternatives]
                healthy_alternatives.extend(same_category[:3 - len(healthy_alternatives)])

            # 여전히 3개 미만이면 다른 카테고리의 건강한 음식 추가
            if len(healthy_alternatives) < 3:
                other_healthy = [f for f in safe_foods if "healthy" in f.get("tags", [])
                                 and f not in healthy_alternatives]
                healthy_alternatives.extend(other_healthy[:3 - len(healthy_alternatives)])

            # 최대 3개 선택
            selected_alternatives = healthy_alternatives[:3]

            for food in selected_alternatives:
                alternatives.append({
                    "name": food["name"],
                    "category": food["category"],
                    "reason": "영양 균형이 더 좋은 건강한 대체 음식입니다.",
                    "nutrition": {
                        "calories": food["calories"],
                        "protein": food["protein"],
                        "fat": food["fat"],
                        "carbs": food["carbs"]
                    }
                })

        # 대체 음식이 없으면 기본 추천
        if not alternatives:
            import random
            other_foods = [f for f in safe_foods if f["name"] != food_name]
            for food in random.sample(other_foods, min(3, len(other_foods))):
                alternatives.append({
                    "name": food["name"],
                    "category": food["category"],
                    "reason": "다양한 식단을 위한 추천 음식입니다.",
                    "nutrition": {
                        "calories": food["calories"],
                        "protein": food["protein"],
                        "fat": food["fat"],
                        "carbs": food["carbs"]
                    }
                })

        logger.info(f"음식 대체 추천 완료: {len(alternatives)}개 대체 음식 추천됨")
        return alternatives

    except Exception as e:
        logger.error(f"음식 대체 추천 중 오류 발생: {str(e)}")
        return []

import logging
from typing import List, Dict, Any, Optional, Tuple
from flask import current_app
from models.user import User
from services.nutrition_analysis import analyze_meal_nutrition, get_food_nutrition

# 이전 코드 생략 (FOOD_DB, RECIPE_DB 등)

def get_recipe_recommendations(ingredients: List[str] = [], meal_type: str = "", health_goal: str = "", allergies: List[str] = []) -> List[Dict[str, Any]]:
    """
    레시피 추천

    Args:
        ingredients (List[str]): 사용 가능한 재료 목록
        meal_type (str): 식사 유형 (아침, 점심, 저녁)
        health_goal (str): 건강 목표
        allergies (List[str]): 알레르기 정보

    Returns:
        List[Dict[str, Any]]: 추천 레시피 목록
    """
    try:
        logger.info("레시피 추천 시작")

        # 알레르기 필터링
        filtered_recipes = []
        for recipe in RECIPE_DB:
            is_safe = True

            # 알레르기 체크
            for allergy in allergies:
                # 재료 목록에서 알레르기 성분 확인
                for ingredient in recipe.get("ingredients", []):
                    if allergy.lower() in ingredient.lower():
                        is_safe = False
                        break

                if not is_safe:
                    break

            # 재료 기반 필터링
            if ingredients:
                # 사용 가능한 재료와 레시피 재료의 교집합 확인
                available_ingredients = set(ingredients)
                recipe_ingredients = set(recipe.get("ingredients", []))
                ingredient_match_ratio = len(available_ingredients.intersection(recipe_ingredients)) / len(recipe_ingredients)

                # 50% 이상의 재료가 일치하는 레시피만 선택
                if ingredient_match_ratio < 0.5:
                    is_safe = False

            # 건강 목표 기반 필터링
            if health_goal and is_safe:
                if "체중 감량" in health_goal.lower():
                    # 저칼로리, 고단백 레시피 선호
                    if recipe.get("calories", 0) > 500 or recipe.get("protein", 0) < 20:
                        is_safe = False

                elif "근육 증가" in health_goal.lower():
                    # 고단백 레시피 선호
                    if recipe.get("protein", 0) < 25:
                        is_safe = False

                elif "당뇨" in health_goal.lower():
                    # 저탄수화물 레시피 선호
                    if recipe.get("carbs", 0) > 30:
                        is_safe = False

            # 식사 유형 기반 필터링
            if meal_type and is_safe:
                if meal_type == "아침":
                    # 아침에 적합한 레시피 (가볍고 에너지 높은 레시피)
                    if recipe.get("time", 0) > 30 or recipe.get("difficulty") == "어려움":
                        is_safe = False

                elif meal_type == "점심":
                    # 점심에 적합한 균형 잡힌 레시피
                    if recipe.get("calories", 0) < 250 or recipe.get("calories", 0) > 600:
                        is_safe = False

                elif meal_type == "저녁":
                    # 저녁에 적합한 레시피 (든든하고 단백질 높은 레시피)
                    if recipe.get("protein", 0) < 20:
                        is_safe = False

            # 안전한 레시피일 경우 추가
            if is_safe:
                filtered_recipes.append(recipe)

        # 추천 로직 (카테고리별로 정렬)
        recommended_recipes = []

        # 1. 건강 목표 기반 추천
        if health_goal:
            goal_specific_recipes = [
                r for r in filtered_recipes
                if any(goal.lower() in str(r.get("health_goals", [])).lower() for goal in health_goal.split())
            ]

            for recipe in goal_specific_recipes[:3]:
                recommended_recipes.append({
                    "title": recipe["title"],
                    "ingredients": recipe["ingredients"],
                    "instructions": recipe["instructions"],
                    "nutrition": {
                        "calories": recipe.get("calories", 0),
                        "protein": recipe.get("protein", 0),
                        "fat": recipe.get("fat", 0),
                        "carbs": recipe.get("carbs", 0)
                    },
                    "time": recipe.get("time", 0),
                    "difficulty": recipe.get("difficulty", ""),
                    "reason": f"{health_goal} 목표에 적합한 레시피입니다."
                })

        # 2. 남은 슬롯에 다양한 레시피 추가
        if len(recommended_recipes) < 3:
            other_recipes = [r for r in filtered_recipes if r not in recommended_recipes]

            for recipe in other_recipes[:3 - len(recommended_recipes)]:
                recommended_recipes.append({
                    "title": recipe["title"],
                    "ingredients": recipe["ingredients"],
                    "instructions": recipe["instructions"],
                    "nutrition": {
                        "calories": recipe.get("calories", 0),
                        "protein": recipe.get("protein", 0),
                        "fat": recipe.get("fat", 0),
                        "carbs": recipe.get("carbs", 0)
                    },
                    "time": recipe.get("time", 0),
                    "difficulty": recipe.get("difficulty", ""),
                    "reason": "다양한 식단을 위한 추천 레시피입니다."
                })

        # 3. 여전히 추천 레시피가 부족하다면 무작위 레시피 추가
        if len(recommended_recipes) < 3:
            import random
            other_recipes = [r for r in RECIPE_DB if r not in recommended_recipes]
            random_recipes = random.sample(other_recipes, min(3 - len(recommended_recipes), len(other_recipes)))

            for recipe in random_recipes:
                recommended_recipes.append({
                    "title": recipe["title"],
                    "ingredients": recipe["ingredients"],
                    "instructions": recipe["instructions"],
                    "nutrition": {
                        "calories": recipe.get("calories", 0),
                        "protein": recipe.get("protein", 0),
                        "fat": recipe.get("fat", 0),
                        "carbs": recipe.get("carbs", 0)
                    },
                    "time": recipe.get("time", 0),
                    "difficulty": recipe.get("difficulty", ""),
                    "reason": "시스템 추천 레시피입니다."
                })

        logger.info(f"레시피 추천 완료: {len(recommended_recipes)}개 레시피 추천됨")
        return recommended_recipes

    except Exception as e:
        logger.error(f"레시피 추천 중 오류 발생: {str(e)}")
        return []

# 추가 유틸리티 함수들

def analyze_daily_nutrition(meals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    하루 식사의 영양 분석

    Args:
        meals (List[Dict[str, Any]]): 하루 동안 섭취한 음식 목록

    Returns:
        Dict[str, Any]: 영양 분석 결과
    """
    try:
        total_calories = 0
        total_protein = 0
        total_fat = 0
        total_carbs = 0

        for meal in meals:
            # 음식 데이터베이스에서 영양 정보 조회
            food = next((f for f in FOOD_DB if f["name"] == meal["name"]), None)

            if food:
                total_calories += food.get("calories", 0)
                total_protein += food.get("protein", 0)
                total_fat += food.get("fat", 0)
                total_carbs += food.get("carbs", 0)

        # 권장 섭취량 대비 비율 계산 (예시 값)
        recommended_calories = 2000  # 일반적인 권장 칼로리
        recommended_protein = 50     # 일일 권장 단백질 섭취량
        recommended_fat = 65         # 일일 권장 지방 섭취량
        recommended_carbs = 300      # 일일 권장 탄수화물 섭취량

        return {
            "total": {
                "calories": total_calories,
                "protein": total_protein,
                "fat": total_fat,
                "carbs": total_carbs
            },
            "percentage": {
                "calories": round((total_calories / recommended_calories) * 100, 2),
                "protein": round((total_protein / recommended_protein) * 100, 2),
                "fat": round((total_fat / recommended_fat) * 100, 2),
                "carbs": round((total_carbs / recommended_carbs) * 100, 2)
            },
            "evaluation": _evaluate_nutrition_balance(
                total_calories, total_protein, total_fat, total_carbs
            )
        }

    except Exception as e:
        logger.error(f"일일 영양 분석 중 오류 발생: {str(e)}")
        return {}

def _evaluate_nutrition_balance(calories, protein, fat, carbs):
    """
    영양 균형 평가 내부 함수

    Args:
        calories (float): 총 칼로리
        protein (float): 총 단백질
        fat (float): 총 지방
        carbs (float): 총 탄수화물

    Returns:
        Dict[str, str]: 영양 균형 평가 결과
    """
    evaluation = {
        "overall": "보통",
        "suggestions": []
    }

    # 칼로리 평가
    if calories < 1500:
        evaluation["overall"] = "부족"
        evaluation["suggestions"].append("칼로리 섭취가 부족합니다. 더 많은 음식을 섭취하세요.")
    elif calories > 2500:
        evaluation["overall"] = "과다"
        evaluation["suggestions"].append("칼로리 섭취가 많습니다. 섭취량을 줄이세요.")

    # 단백질 평가 (일일 권장량 50g 기준)
    if protein < 40:
        evaluation["suggestions"].append("단백질 섭취가 부족합니다. 고단백 식품을 추가하세요.")
    elif protein > 100:
        evaluation["suggestions"].append("단백질 섭취가 과다합니다. 섭취량을 조절하세요.")

    # 지방 평가 (일일 권장량 65g 기준)
    if fat < 30:
        evaluation["suggestions"].append("지방 섭취가 부족합니다. 건강한 지방 섭취를 늘리세요.")
    elif fat > 100:
        evaluation["suggestions"].append("지방 섭취가 과다합니다. 섭취량을 줄이세요.")

    # 탄수화물 평가 (일일 권장량 300g 기준)
    if carbs < 200:
        evaluation["suggestions"].append("탄수화물 섭취가 부족합니다. 에너지 공급을 늘리세요.")
    elif carbs > 400:
        evaluation["suggestions"].append("탄수화물 섭취가 과다합니다. 섭취량을 조절하세요.")

    return evaluation

# 예외 처리 및 로깅 설정
def setup_nutrition_logging():
    """
    영양 관련 로깅 설정
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('nutrition_service.log')
        ]
    )
    return logger

# 모듈 초기화
logger = setup_nutrition_logging()