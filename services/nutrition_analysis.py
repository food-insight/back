import logging
from typing import List, Dict, Any, Optional, Tuple
from flask import current_app
from models.user import User

# 로깅 설정
logger = logging.getLogger(__name__)

# 샘플 음식 영양 데이터베이스 (실제 구현에서는 데이터베이스에서 조회)
FOOD_NUTRITION_DB = {
    "김치찌개": {"calories": 250, "carbs": 10, "protein": 15, "fat": 12, "sodium": 1200, "fiber": 3, "sugar": 4},
    "불고기": {"calories": 400, "carbs": 10, "protein": 30, "fat": 25, "sodium": 800, "fiber": 1, "sugar": 8},
    "비빔밥": {"calories": 600, "carbs": 80, "protein": 20, "fat": 15, "sodium": 900, "fiber": 5, "sugar": 6},
    "김치": {"calories": 30, "carbs": 6, "protein": 1, "fat": 0.2, "sodium": 500, "fiber": 2, "sugar": 3},
    "떡볶이": {"calories": 450, "carbs": 80, "protein": 8, "fat": 12, "sodium": 1100, "fiber": 2, "sugar": 15},
    "라면": {"calories": 500, "carbs": 70, "protein": 10, "fat": 20, "sodium": 1800, "fiber": 1, "sugar": 2},
    "김밥": {"calories": 350, "carbs": 65, "protein": 10, "fat": 8, "sodium": 700, "fiber": 3, "sugar": 5},
    "삼겹살": {"calories": 500, "carbs": 0, "protein": 25, "fat": 42, "sodium": 600, "fiber": 0, "sugar": 0},
    "치킨": {"calories": 450, "carbs": 15, "protein": 35, "fat": 30, "sodium": 1000, "fiber": 0, "sugar": 1},
    "된장찌개": {"calories": 200, "carbs": 8, "protein": 12, "fat": 10, "sodium": 1000, "fiber": 4, "sugar": 2},
    "갈비탕": {"calories": 350, "carbs": 10, "protein": 28, "fat": 22, "sodium": 900, "fiber": 1, "sugar": 2},
    "냉면": {"calories": 480, "carbs": 85, "protein": 15, "fat": 5, "sodium": 1200, "fiber": 3, "sugar": 6},
    "잡채": {"calories": 320, "carbs": 45, "protein": 10, "fat": 15, "sodium": 600, "fiber": 4, "sugar": 8},
    "돈까스": {"calories": 550, "carbs": 40, "protein": 25, "fat": 35, "sodium": 700, "fiber": 2, "sugar": 3},
    "제육볶음": {"calories": 450, "carbs": 15, "protein": 30, "fat": 28, "sodium": 850, "fiber": 2, "sugar": 10},
    "쌀밥": {"calories": 300, "carbs": 65, "protein": 5, "fat": 0.5, "sodium": 10, "fiber": 1, "sugar": 0},
    "잔치국수": {"calories": 400, "carbs": 75, "protein": 12, "fat": 5, "sodium": 1000, "fiber": 2, "sugar": 3},
    "만두": {"calories": 350, "carbs": 40, "protein": 15, "fat": 12, "sodium": 600, "fiber": 2, "sugar": 2},
}

def analyze_meal_nutrition(food_names: List[str]) -> Dict[str, float]:
    """
    식사의 영양 성분 분석

    Args:
        food_names (List[str]): 음식 이름 목록

    Returns:
        Dict[str, float]: 영양 성분 정보
    """
    try:
        logger.info(f"식사 영양 분석 시작: {', '.join(food_names)}")

        if not food_names:
            logger.warning("분석할 음식이 없습니다.")
            return {}

        # 초기 영양 성분 집계
        total_nutrition = {
            "calories": 0,
            "carbs": 0,
            "protein": 0,
            "fat": 0,
            "sodium": 0,
            "fiber": 0,
            "sugar": 0
        }

        # 영양 성분 합산
        found_foods = 0
        for food_name in food_names:
            # 데이터베이스에서 음식 찾기
            nutrition = FOOD_NUTRITION_DB.get(food_name)

            if nutrition:
                found_foods += 1
                for key, value in nutrition.items():
                    if key in total_nutrition:
                        total_nutrition[key] += value
            else:
                logger.warning(f"'{food_name}'의 영양 정보를 찾을 수 없습니다.")

        # 평균 영양 성분 계산 (데이터가 없는 경우 처리)
        if found_foods == 0:
            logger.warning("영양 정보가 있는 음식이 없습니다.")
            return {}

        logger.info(f"식사 영양 분석 완료: {found_foods}/{len(food_names)} 음식 분석됨")
        return total_nutrition

    except Exception as e:
        logger.error(f"식사 영양 분석 중 오류 발생: {str(e)}")
        return {}

def get_nutrition_insights(nutrition_data: Dict[str, float], user: Optional[User], is_average: bool = False) -> List[Dict[str, Any]]:
    """
    영양 데이터 기반 인사이트 생성

    Args:
        nutrition_data (Dict[str, float]): 영양 데이터
        user (Optional[User]): 사용자 정보
        is_average (bool): 평균 데이터 여부

    Returns:
        List[Dict[str, Any]]: 인사이트 목록
    """
    try:
        if not nutrition_data:
            return []

        insights = []

        # 사용자별 목표 영양소 계산
        target_nutrients = calculate_target_nutrients(user)

        # 칼로리 인사이트
        if "calories" in nutrition_data:
            calories = nutrition_data["calories"]
            calories_target = target_nutrients.get("calories", 2000)
            calories_percentage = round((calories / calories_target) * 100, 1) if calories_target > 0 else 0

            if is_average:
                calories_text = "일일 평균"
            else:
                calories_text = "이번 식사의"

            if calories_percentage > 40:  # 한 끼 기준 40% 이상은 과다
                insights.append({
                    "type": "warning",
                    "title": "칼로리 과다 섭취",
                    "content": f"{calories_text} 칼로리({calories}kcal)는 일일 권장량({calories_target}kcal)의 {calories_percentage}%입니다. 다음 식사에서 칼로리를 줄이는 것이 좋습니다."
                })
            elif calories_percentage < 20 and not is_average:  # 한 끼 기준 20% 미만은 부족 (평균 데이터가 아닐 경우)
                insights.append({
                    "type": "info",
                    "title": "칼로리 섭취 부족",
                    "content": f"{calories_text} 칼로리({calories}kcal)는 일일 권장량({calories_target}kcal)의 {calories_percentage}%입니다. 영양 균형을 위해 추가 섭취를 고려하세요."
                })
            else:
                insights.append({
                    "type": "success",
                    "title": "적절한 칼로리 섭취",
                    "content": f"{calories_text} 칼로리({calories}kcal)는 일일 권장량({calories_target}kcal)의 {calories_percentage}%로 적절한 수준입니다."
                })

        # 단백질 인사이트
        if "protein" in nutrition_data:
            protein = nutrition_data["protein"]
            protein_target = target_nutrients.get("protein", 60)
            protein_percentage = round((protein / protein_target) * 100, 1) if protein_target > 0 else 0

            if is_average:
                if protein_percentage < 80:
                    insights.append({
                        "type": "warning",
                        "title": "단백질 섭취 부족",
                        "content": f"일일 평균 단백질 섭취량({protein}g)은 권장량({protein_target}g)의 {protein_percentage}%입니다. 단백질이 풍부한 식품을 더 섭취하세요."
                    })
            elif protein_percentage < 20 and not is_average:  # 한 끼 기준
                insights.append({
                    "type": "info",
                    "title": "단백질 섭취 부족",
                    "content": f"이번 식사의 단백질({protein}g)은 일일 권장량({protein_target}g)의 {protein_percentage}%입니다. 다음 식사에서 단백질 섭취를 늘리는 것이 좋습니다."
                })

        # 탄수화물 인사이트
        if "carbs" in nutrition_data:
            carbs = nutrition_data["carbs"]
            carbs_target = target_nutrients.get("carbs", 275)
            carbs_percentage = round((carbs / carbs_target) * 100, 1) if carbs_target > 0 else 0

            if is_average and carbs_percentage > 110:
                insights.append({
                    "type": "info",
                    "title": "탄수화물 과다 섭취",
                    "content": f"일일 평균 탄수화물 섭취량({carbs}g)은 권장량({carbs_target}g)의 {carbs_percentage}%입니다. 탄수화물 섭취를 줄이는 것이 좋습니다."
                })

        # 나트륨 인사이트
        if "sodium" in nutrition_data:
            sodium = nutrition_data["sodium"]
            sodium_target = target_nutrients.get("sodium", 2000)
            sodium_percentage = round((sodium / sodium_target) * 100, 1) if sodium_target > 0 else 0

            if sodium_percentage > 50 and not is_average:  # 한 끼 기준 50% 이상
                insights.append({
                    "type": "warning",
                    "title": "나트륨 과다 섭취",
                    "content": f"이번 식사의 나트륨({sodium}mg)은 일일 권장량({sodium_target}mg)의 {sodium_percentage}%입니다. 과도한 나트륨 섭취는 고혈압 위험을 증가시킬 수 있습니다."
                })
            elif is_average and sodium_percentage > 100:
                insights.append({
                    "type": "warning",
                    "title": "나트륨 과다 섭취",
                    "content": f"일일 평균 나트륨 섭취량({sodium}mg)은 권장량({sodium_target}mg)의 {sodium_percentage}%입니다. 가공식품과 소금 섭취를 줄이는 것이 좋습니다."
                })

        # 지방 인사이트
        if "fat" in nutrition_data:
            fat = nutrition_data["fat"]
            fat_target = target_nutrients.get("fat", 65)
            fat_percentage = round((fat / fat_target) * 100, 1) if fat_target > 0 else 0

            if is_average and fat_percentage > 110:
                insights.append({
                    "type": "info",
                    "title": "지방 과다 섭취",
                    "content": f"일일 평균 지방 섭취량({fat}g)은 권장량({fat_target}g)의 {fat_percentage}%입니다. 포화지방과 트랜스지방 섭취를 줄이는 것이 좋습니다."
                })

        # 영양 균형 인사이트
        if all(key in nutrition_data for key in ["carbs", "protein", "fat"]):
            total_macros = nutrition_data["carbs"] + nutrition_data["protein"] + nutrition_data["fat"]
            if total_macros > 0:
                carbs_ratio = round((nutrition_data["carbs"] / total_macros) * 100)
                protein_ratio = round((nutrition_data["protein"] / total_macros) * 100)
                fat_ratio = round((nutrition_data["fat"] / total_macros) * 100)

                # 이상적인 비율: 탄수화물 45-65%, 단백질 10-35%, 지방 20-35%
                balanced = (45 <= carbs_ratio <= 65) and (10 <= protein_ratio <= 35) and (20 <= fat_ratio <= 35)

                if balanced and is_average:
                    insights.append({
                        "type": "success",
                        "title": "균형 잡힌 영양소 비율",
                        "content": f"탄수화물({carbs_ratio}%), 단백질({protein_ratio}%), 지방({fat_ratio}%)의 비율이 적절하게 균형을 이루고 있습니다."
                    })
                elif not balanced and is_average:
                    insights.append({
                        "type": "info",
                        "title": "영양소 비율 개선 필요",
                        "content": f"현재 탄수화물({carbs_ratio}%), 단백질({protein_ratio}%), 지방({fat_ratio}%)의 비율입니다. 이상적인 비율은 탄수화물(45-65%), 단백질(10-35%), 지방(20-35%)입니다."
                    })

        return insights

    except Exception as e:
        logger.error(f"영양 인사이트 생성 중 오류 발생: {str(e)}")
        return []

def calculate_target_nutrients(user: Optional[User] = None) -> Dict[str, float]:
    """
    사용자별 목표 영양소 계산

    Args:
        user (Optional[User]): 사용자 정보

    Returns:
        Dict[str, float]: 목표 영양소 정보
    """
    # 기본 영양소 목표 (성인 여성 기준)
    default_targets = {
        "calories": 2000,
        "protein": 60,
        "carbs": 275,
        "fat": 65,
        "sodium": 2000,
        "fiber": 25,
        "sugar": 50
    }

    if not user:
        return default_targets

    # 사용자 정보에 따른 조정
    try:
        targets = default_targets.copy()

        # 성별에 따른 조정
        if user.gender == 0:  # 남성
            targets["calories"] = 2500
            targets["protein"] = 70
            targets["carbs"] = 325
            targets["fat"] = 80

        # 나이에 따른 조정
        age = user.calculate_age()
        if age:
            if age < 18:
                # 청소년은 칼로리와 단백질 더 필요
                targets["calories"] += 300
                targets["protein"] += 10
            elif age > 60:
                # 노인은 칼로리 요구량 감소
                targets["calories"] -= 200

        # 건강 목표에 따른 조정
        if user.health_goal:
            health_goal = user.health_goal.lower()

            if "체중 감량" in health_goal or "다이어트" in health_goal:
                # 체중 감량 - 칼로리 20% 감소, 단백질 유지/증가, 탄수화물/지방 감소
                targets["calories"] *= 0.8
                targets["protein"] *= 1.1
                targets["carbs"] *= 0.7
                targets["fat"] *= 0.7

            elif "근육 증가" in health_goal or "벌크업" in health_goal:
                # 근육 증가 - 칼로리 20% 증가, 단백질 50% 증가, 탄수화물 20% 증가
                targets["calories"] *= 1.2
                targets["protein"] *= 1.5
                targets["carbs"] *= 1.2

            elif "당뇨" in health_goal:
                # 당뇨 관리 - 탄수화물 감소, 당 감소
                targets["carbs"] *= 0.7
                targets["sugar"] *= 0.5

            elif "고혈압" in health_goal:
                # 고혈압 관리 - 나트륨 감소
                targets["sodium"] *= 0.6

        # 값 반올림
        for key in targets:
            targets[key] = round(targets[key])

        return targets

    except Exception as e:
        logger.error(f"목표 영양소 계산 중 오류 발생: {str(e)}")
        return default_targets

def calculate_daily_nutrition(meals_nutrition: List[Dict[str, float]]) -> Dict[str, float]:
    """
    여러 식사의 일일 영양 총합 계산

    Args:
        meals_nutrition (List[Dict[str, float]]): 식사별 영양 정보 목록

    Returns:
        Dict[str, float]: 일일 영양 총합
    """
    try:
        # 모든 영양소 키 수집
        all_keys = set()
        for meal in meals_nutrition:
            all_keys.update(meal.keys())

        # 영양소별 합계 계산
        daily_nutrition = {key: 0 for key in all_keys}

        for meal in meals_nutrition:
            for key, value in meal.items():
                daily_nutrition[key] += value

        # 값 반올림
        for key in daily_nutrition:
            if isinstance(daily_nutrition[key], float):
                daily_nutrition[key] = round(daily_nutrition[key], 1)

        return daily_nutrition

    except Exception as e:
        logger.error(f"일일 영양 총합 계산 중 오류 발생: {str(e)}")
        return {}

def compare_nutrition_data(current: Dict[str, float], previous: Dict[str, float]) -> Dict[str, Dict[str, Any]]:
    """
    현재 영양 데이터와 이전 데이터 비교

    Args:
        current (Dict[str, float]): 현재 영양 데이터
        previous (Dict[str, float]): 이전 영양 데이터

    Returns:
        Dict[str, Dict[str, Any]]: 비교 결과
    """
    try:
        if not current or not previous:
            return {}

        comparison = {}

        # 공통 키에 대해 비교
        common_keys = set(current.keys()) & set(previous.keys())

        for key in common_keys:
            curr_val = current[key]
            prev_val = previous[key]

            # 변화량 계산
            change = curr_val - prev_val

            # 변화율 계산 (0으로 나누기 방지)
            if prev_val != 0:
                percentage = round((change / prev_val) * 100, 1)
            else:
                percentage = 0 if change == 0 else float('inf')

            # 추세 결정
            if abs(percentage) < 5:  # 5% 미만 변화는 유지로 간주
                trend = "same"
            else:
                trend = "up" if change > 0 else "down"

            comparison[key] = {
                "current": curr_val,
                "previous": prev_val,
                "change": change,
                "percentage": percentage,
                "trend": trend
            }

        return comparison

    except Exception as e:
        logger.error(f"영양 데이터 비교 중 오류 발생: {str(e)}")
        return {}

def get_food_nutrition(food_name: str) -> Dict[str, Any]:
    """
    음식의 영양 정보 조회

    Args:
        food_name (str): 음식 이름

    Returns:
        Dict[str, Any]: 영양 정보
    """
    try:
        # 데이터베이스에서 음식 영양 정보 조회
        nutrition = FOOD_NUTRITION_DB.get(food_name)

        if nutrition:
            return {
                "name": food_name,
                "nutrition": nutrition
            }
        else:
            logger.warning(f"'{food_name}'의 영양 정보를 찾을 수 없습니다.")
            return {
                "name": food_name,
                "nutrition": {}
            }

    except Exception as e:
        logger.error(f"음식 영양 정보 조회 중 오류 발생: {str(e)}")
        return {
            "name": food_name,
            "nutrition": {}
        }