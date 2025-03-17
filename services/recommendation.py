import logging
from typing import List, Dict, Any, Optional, Tuple
from flask import current_app
from models.user import User
from services.food_database import FoodDatabaseService
from services.rag_service import RAGService

# 로깅 설정
logger = logging.getLogger(__name__)

class RecommendationService:
    """
    식품 추천 및 레시피 추천 서비스
    """
    def __init__(self, food_db=None, rag_service=None):
        """
        추천 서비스 초기화

        Args:
            food_db (Optional[FoodDatabaseService]): 식품 데이터베이스 서비스
            rag_service (Optional[RAGService]): RAG 서비스
        """
        self.food_db = food_db or FoodDatabaseService()
        self.rag_service = rag_service or RAGService()

    def get_similar_foods(self, food_name: str, limit=5):
        """
        유사한 식품 추천

        Args:
            food_name: 기준 식품 이름
            limit: 반환할 추천 수

        Returns:
            dict: 유사한 식품 목록 포함 정보
        """
        # 데이터베이스에서 식품 정보 조회
        food_info = self.food_db.get_food_by_name(food_name)

        if food_info:
            # 데이터베이스 기반 유사 식품 찾기 (예: 카테고리, 영양소 등 기준)
            similar_foods = self.food_db.get_similar_foods(
                food_name=food_name,
                category=food_info.get('category'),
                limit=limit
            )
            return {
                "reference_food": food_name,
                "similar_foods": similar_foods,
                "source": "database"
            }
        else:
            # RAG 시스템 기반 유사 식품 찾기
            rag_result = self.rag_service.query_food_info(
                f"{food_name}과 유사한 음식 {limit}개 추천"
            )
            return {
                "reference_food": food_name,
                "similar_foods": self._parse_rag_recommendations(rag_result),
                "source": "rag"
            }

    def generate_meal_recommendations(self, user: Optional[User], allergies: List[str] = [], recent_foods: List[str] = []) -> Dict[str, List[Dict[str, Any]]]:
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

            # 건강 목표 기반 쿼리 생성
            health_goal_query = ""
            if user and user.health_goal:
                health_goal = user.health_goal.lower()
                health_goal_query = f"건강 목표: {health_goal}"

                if "체중 감량" in health_goal or "다이어트" in health_goal:
                    health_goal_query += ", 저칼로리 고단백 식품"
                elif "근육 증가" in health_goal or "벌크업" in health_goal:
                    health_goal_query += ", 고단백 고칼로리 식품"
                elif "당뇨" in health_goal:
                    health_goal_query += ", 저탄수화물 식품"
                elif "고혈압" in health_goal:
                    health_goal_query += ", 저나트륨 식품"

            # 알레르기 정보 추가
            if allergies:
                health_goal_query += f", 알레르기 제외: {', '.join(allergies)}"

            # RAG 활용 건강 기반 추천
            if health_goal_query:
                try:
                    rag_result = self.rag_service.query_food_info(
                        f"다음 조건에 맞는 식품 추천: {health_goal_query}"
                    )
                    health_recommendations = self._parse_rag_recommendations(rag_result)

                    # 데이터베이스에서 추가 정보 보강
                    for rec in health_recommendations:
                        food_name = rec.get("name", "")
                        food_info = self.food_db.get_food_by_name(food_name)
                        if food_info:
                            rec["details"] = food_info
                            rec["source"] = "database"
                        else:
                            rec["source"] = "rag"

                    recommendations["health_based"] = health_recommendations[:3]
                except Exception as e:
                    logger.error(f"건강 기반 추천 중 오류: {str(e)}")

            # 균형 잡힌 식단 추천
            try:
                balanced_query = "균형 잡힌 한식 식단 조합 3가지 추천"
                if allergies:
                    balanced_query += f", 제외 재료: {', '.join(allergies)}"

                rag_result = self.rag_service.query_food_info(balanced_query)
                balanced_recommendations = self._parse_balanced_meal(rag_result)

                # 데이터베이스에서 각 구성요소 정보 보강
                for meal in balanced_recommendations:
                    components = []
                    for component in meal.get("components", []):
                        food_name = component.get("name", "")
                        food_info = self.food_db.get_food_by_name(food_name)
                        if food_info:
                            component["details"] = food_info
                            component["source"] = "database"
                        else:
                            component["source"] = "rag"
                        components.append(component)
                    meal["components"] = components

                recommendations["balanced_meal"] = balanced_recommendations[:3]
            except Exception as e:
                logger.error(f"균형 잡힌 식단 추천 중 오류: {str(e)}")

            # 다양성 기반 추천 (최근에 먹지 않은 음식)
            try:
                # 데이터베이스에서 모든 음식 가져오기
                all_foods = self.food_db.get_all_foods(limit=50)  # 적절한 수로 제한

                # 최근 먹은 음식 제외
                recent_food_set = set(recent_foods)
                not_recent_foods = [f for f in all_foods if f.get("name") not in recent_food_set]

                # 추천 생성
                import random
                selected_foods = random.sample(
                    not_recent_foods,
                    min(3, len(not_recent_foods))
                ) if not_recent_foods else []

                variety_based = []
                for food in selected_foods:
                    variety_based.append({
                        "name": food.get("name", ""),
                        "category": food.get("category", ""),
                        "reason": "최근에 드시지 않은 음식으로, 식단의 다양성을 높여줍니다.",
                        "details": food,
                        "source": "database"
                    })

                # 충분한 추천이 없으면 RAG 시스템 사용
                if len(variety_based) < 3:
                    variety_query = "다양한 한식 추천"
                    if recent_foods:
                        variety_query += f", 최근 먹은 음식 제외: {', '.join(recent_foods[:5])}"

                    rag_result = self.rag_service.query_food_info(variety_query)
                    rag_recommendations = self._parse_rag_recommendations(rag_result)

                    # 이미 추천된 음식 제외
                    existing_names = {item.get("name", "") for item in variety_based}
                    filtered_recs = [r for r in rag_recommendations if r.get("name", "") not in existing_names]

                    # 데이터베이스에서 추가 정보 보강
                    for rec in filtered_recs:
                        food_name = rec.get("name", "")
                        food_info = self.food_db.get_food_by_name(food_name)
                        if food_info:
                            rec["details"] = food_info
                            rec["source"] = "database"
                        else:
                            rec["source"] = "rag"

                    variety_based.extend(filtered_recs[:3 - len(variety_based)])

                recommendations["variety_based"] = variety_based
            except Exception as e:
                logger.error(f"다양성 기반 추천 중 오류: {str(e)}")

            logger.info(f"식단 추천 생성 완료: {sum(len(recs) for recs in recommendations.values())}개 추천")
            return recommendations

        except Exception as e:
            logger.error(f"식단 추천 생성 중 오류 발생: {str(e)}")
            return {
                "health_based": [],
                "balanced_meal": [],
                "variety_based": []
            }

    def generate_food_alternatives(self, food_name: str, reason: str = "건강한 대체 음식", allergies: List[str] = []) -> List[Dict[str, Any]]:
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
            original_food = self.food_db.get_food_by_name(food_name)

            # 쿼리 구성
            alternatives_query = f"{food_name}의 대체 음식 추천"
            if reason:
                alternatives_query += f", 이유: {reason}"
            if allergies:
                alternatives_query += f", 알레르기 제외: {', '.join(allergies)}"

            # RAG로 대체 음식 추천 받기
            rag_result = self.rag_service.query_food_info(alternatives_query)
            alternative_foods = self._parse_rag_recommendations(rag_result)

            # 대체 음식에 대한 추가 정보 조회
            for alt_food in alternative_foods:
                food_name = alt_food.get("name", "")
                food_info = self.food_db.get_food_by_name(food_name)

                if food_info:
                    alt_food["details"] = food_info
                    alt_food["source"] = "database"

                    # 원본 음식이 있는 경우 비교 정보 제공
                    if original_food and "nutrients" in original_food and "nutrients" in food_info:
                        alt_food["comparison"] = self._compare_nutrition(
                            original_food["nutrients"],
                            food_info["nutrients"]
                        )
                else:
                    alt_food["source"] = "rag"

            logger.info(f"음식 대체 추천 완료: {len(alternative_foods)}개 대체 음식 추천됨")
            return alternative_foods[:3]  # 최대 3개 반환

        except Exception as e:
            logger.error(f"음식 대체 추천 중 오류 발생: {str(e)}")
            return []

    def get_recipe_recommendations(self, ingredients: List[str] = [], meal_type: str = "", health_goal: str = "", allergies: List[str] = []) -> List[Dict[str, Any]]:
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

            # 쿼리 구성
            recipe_query = "레시피 추천"

            if meal_type:
                recipe_query += f", 식사: {meal_type}"

            if health_goal:
                recipe_query += f", 목표: {health_goal}"

            if ingredients:
                recipe_query += f", 재료: {', '.join(ingredients[:5])}"
                if len(ingredients) > 5:
                    recipe_query += f" 외 {len(ingredients) - 5}개"

            if allergies:
                recipe_query += f", 알레르기 제외: {', '.join(allergies)}"

            # RAG를 통한 레시피 추천
            rag_result = self.rag_service.query_food_info(recipe_query)

            # 결과 파싱 및 구조화
            recommended_recipes = self._parse_recipes(rag_result)

            logger.info(f"레시피 추천 완료: {len(recommended_recipes)}개 레시피 추천됨")
            return recommended_recipes[:3]  # 최대 3개 반환

        except Exception as e:
            logger.error(f"레시피 추천 중 오류 발생: {str(e)}")
            return []

    def recommend_balanced_meal(self, preferences=None, dietary_restrictions=None):
        """
        균형 잡힌 식사 추천

        Args:
            preferences: 사용자 선호도
            dietary_restrictions: 식이 제한 사항

        Returns:
            dict: 추천 식단 정보
        """
        # 선호도와 제한 사항을 쿼리로 구성
        query = "균형 잡힌 식사 추천"
        if preferences:
            query += f", 선호: {', '.join(preferences)}"
        if dietary_restrictions:
            query += f", 제한: {', '.join(dietary_restrictions)}"

        # RAG 시스템을 통해 추천 받기
        rag_result = self.rag_service.query_food_info(query)

        # 추천된 식품 목록에 대한 상세 정보 조회
        meal_plan = self._parse_meal_plan(rag_result)
        enriched_meal_plan = self._enrich_meal_plan(meal_plan)

        return {
            "meal_plan": enriched_meal_plan,
            "reasoning": rag_result,
            "preferences": preferences,
            "dietary_restrictions": dietary_restrictions
        }

    def analyze_daily_nutrition(self, meals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        하루 식사의 영양 분석

        Args:
            meals (List[Dict[str, Any]]): 하루 동안 섭취한 음식 목록

        Returns:
            Dict[str, Any]: 영양 분석 결과
        """
        try:
            # 영양소 초기화
            total_nutrition = {
                "calories": 0,
                "protein": 0,
                "fat": 0,
                "carbs": 0,
                "sodium": 0,
                "fiber": 0,
                "sugar": 0
            }

            # 각 음식의 영양 정보 합산
            for meal in meals:
                food_name = meal.get("name", "")
                food_info = self.food_db.get_food_by_name(food_name)

                if food_info and "nutrients" in food_info:
                    nutrients = food_info["nutrients"]
                    for key in total_nutrition:
                        if key in nutrients:
                            total_nutrition[key] += nutrients[key]

            # 권장 섭취량 (예시)
            recommended = {
                "calories": 2000,
                "protein": 50,
                "fat": 65,
                "carbs": 300,
                "sodium": 2000,
                "fiber": 25,
                "sugar": 50
            }

            # 권장량 대비 비율 계산
            percentage = {}
            for key in total_nutrition:
                if key in recommended and recommended[key] > 0:
                    percentage[key] = round((total_nutrition[key] / recommended[key]) * 100, 2)
                else:
                    percentage[key] = 0

            # 영양 평가
            evaluation = self._evaluate_nutrition_balance(total_nutrition, recommended)

            return {
                "total": total_nutrition,
                "percentage": percentage,
                "evaluation": evaluation
            }

        except Exception as e:
            logger.error(f"일일 영양 분석 중 오류 발생: {str(e)}")
            return {}

    def _parse_rag_recommendations(self, rag_result):
        """RAG 결과에서 추천 식품 목록 추출"""
        try:
            # 간단한 구현 - 실제로는 LLM을 사용하여 구조화할 수 있음
            # 예시: "1. 사과, 2. 바나나, 3. 오렌지" -> ["사과", "바나나", "오렌지"]
            # 더 복잡한 구현 필요

            lines = rag_result.split("\n")
            recommendations = []

            for line in lines:
                if ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        name = parts[1].strip()
                        reason = parts[0].strip()
                        if name:
                            recommendations.append({"name": name, "reason": reason})
                elif "." in line:
                    parts = line.split(".", 1)
                    if len(parts) > 1 and parts[0].strip().isdigit():
                        name = parts[1].strip()
                        if name:
                            recommendations.append({"name": name})
                elif "-" in line:
                    parts = line.split("-", 1)
                    if len(parts) > 1:
                        name = parts[1].strip()
                        if name:
                            recommendations.append({"name": name})

            return recommendations
        except Exception as e:
            logger.error(f"추천 결과 파싱 중 오류: {str(e)}")
            return []

    def _parse_balanced_meal(self, rag_result):
        """RAG 결과에서 균형 잡힌 식단 추출"""
        try:
            lines = rag_result.split("\n")
            meals = []
            current_meal = None

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # 새로운 식단 조합 시작
                if line.startswith("식단") or line.startswith("1.") or line.startswith("2.") or line.startswith("3."):
                    if current_meal:
                        meals.append(current_meal)

                    current_meal = {
                        "name": line.split(":", 1)[-1].strip() if ":" in line else line,
                        "components": []
                    }

                # 구성 음식 추가
                elif current_meal and (":" in line or "-" in line or "•" in line):
                    delimiter = ":" if ":" in line else "-" if "-" in line else "•"
                    parts = line.split(delimiter, 1)

                    if len(parts) > 1:
                        category = parts[0].strip()
                        name = parts[1].strip()

                        if name:
                            current_meal["components"].append({
                                "name": name,
                                "category": category
                            })

            # 마지막 식단 추가
            if current_meal and current_meal not in meals:
                meals.append(current_meal)

            # 각 식단에 이유 추가
            for meal in meals:
                meal["reason"] = "영양 균형이 잘 맞는 한식 식단입니다."

            return meals
        except Exception as e:
            logger.error(f"식단 조합 파싱 중 오류: {str(e)}")
            return []

    def _parse_meal_plan(self, rag_result):
        """RAG 결과에서 식단 계획 추출"""
        try:
            meal_plan = {
                "breakfast": [],
                "lunch": [],
                "dinner": [],
                "snacks": []
            }

            current_meal = None
            for line in rag_result.split("\n"):
                line = line.strip().lower()
                if not line:
                    continue

                if "아침" in line or "breakfast" in line:
                    current_meal = "breakfast"
                elif "점심" in line or "lunch" in line:
                    current_meal = "lunch"
                elif "저녁" in line or "dinner" in line:
                    current_meal = "dinner"
                elif "간식" in line or "snack" in line:
                    current_meal = "snacks"
                elif current_meal and (":" in line or "-" in line or "•" in line):
                    # 식품 항목으로 간주
                    food_name = line.split(":", 1)[-1].strip() if ":" in line else line.split("-", 1)[-1].strip()
                    food_name = food_name.split("•", 1)[-1].strip()
                    if food_name:
                        meal_plan[current_meal].append(food_name)

            return meal_plan
        except Exception as e:
            logger.error(f"식단 계획 파싱 중 오류: {str(e)}")
            return {
                "breakfast": [],
                "lunch": [],
                "dinner": [],
                "snacks": []
            }

    def _enrich_meal_plan(self, meal_plan):
        """식단 계획의 각 식품에 대한 상세 정보 추가"""
        enriched_plan = {}

        for meal, foods in meal_plan.items():
            enriched_foods = []
            for food_name in foods:
                food_info = self.food_db.get_food_by_name(food_name)
                if food_info:
                    enriched_foods.append({
                        "name": food_name,
                        "details": food_info,
                        "source": "database"
                    })
                else:
                    # 데이터베이스에 없는 경우 RAG 시스템 활용
                    rag_info = self.rag_service.query_food_info(f"{food_name}의 영양 정보")
                    enriched_foods.append({
                        "name": food_name,
                        "details": {"description": rag_info},
                        "source": "rag"
                    })
            enriched_plan[meal] = enriched_foods

        return enriched_plan

    def _parse_recipes(self, rag_result):
        """RAG 결과에서 레시피 정보 추출"""
        try:
            lines = rag_result.split("\n")
            recipes = []
            current_recipe = None
            current_section = None

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # 새 레시피 시작
                if line.startswith("레시피") or line.startswith("1.") or line.startswith("2.") or line.startswith("3."):
                    if current_recipe:
                        recipes.append(current_recipe)

                    title = line.split(":", 1)[-1].strip() if ":" in line else line
                    current_recipe = {
                        "title": title,
                        "ingredients": [],
                        "instructions": "",
                        "nutrition": {},
                        "reason": ""
                    }
                    current_section = None

                # 섹션 식별
                elif line.lower().startswith("재료") or line.lower().startswith("ingredients"):
                    current_section = "ingredients"
                elif line.lower().startswith("조리법") or line.lower().startswith("instructions") or line.lower().startswith("만드는 방법"):
                    current_section = "instructions"
                elif line.lower().startswith("영양정보") or line.lower().startswith("nutrition"):
                    current_section = "nutrition"
                elif line.lower().startswith("추천이유") or line.lower().startswith("reason"):
                    current_section = "reason"

                # 섹션 내용 추가
                elif current_recipe and current_section:
                    if current_section == "ingredients" and (":" in line or "-" in line or "•" in line):
                        delimiter = ":" if ":" in line else "-" if "-" in line else "•"
                        ingredient = line.split(delimiter, 1)[-1].strip()
                        if ingredient:
                            current_recipe["ingredients"].append(ingredient)
                    elif current_section == "instructions":
                        if current_recipe["instructions"]:
                            current_recipe["instructions"] += "\n"
                        current_recipe["instructions"] += line
                    elif current_section == "nutrition" and ":" in line:
                        key, value = line.split(":", 1)
                        key = key.strip().lower()
                        value_str = value.strip()

                        # 숫자 추출
                        import re
                        num_match = re.search(r'\d+', value_str)
                        if num_match:
                            num_value = int(num_match.group())
                            if "칼로리" in key or "calories" in key:
                                current_recipe["nutrition"]["calories"] = num_value
                            elif "단백질" in key or "protein" in key:
                                current_recipe["nutrition"]["protein"] = num_value
                            elif "탄수화물" in key or "carbs" in key:
                                current_recipe["nutrition"]["carbs"] = num_value
                            elif "지방" in key or "fat" in key:
                                current_recipe["nutrition"]["fat"] = num_value
                    elif current_section == "reason":
                        if current_recipe["reason"]:
                            current_recipe["reason"] += " "
                        current_recipe["reason"] += line

            # 마지막 레시피 추가
            if current_recipe and current_recipe not in recipes:
                recipes.append(current_recipe)

            return recipes
        except Exception as e:
            logger.error(f"레시피 파싱 중 오류: {str(e)}")
            return []

    def _compare_nutrition(self, original_nutrition, alternative_nutrition):
        """영양소 비교"""
        result = {}

        for key in original_nutrition:
            if key in alternative_nutrition:
                orig_val = original_nutrition[key]
                alt_val = alternative_nutrition[key]

                if isinstance(orig_val, (int, float)) and isinstance(alt_val, (int, float)):
                    change = alt_val - orig_val
                    if orig_val != 0:
                        percentage = round((change / orig_val) * 100, 1)
                    else:
                        percentage = float('inf') if change > 0 else 0

                    result[key] = {
                        "original": orig_val,
                        "alternative": alt_val,
                        "change": change,
                        "percentage": percentage,
                        "direction": "up" if change > 0 else "down" if change < 0 else "same"
                    }

        return result

    def _evaluate_nutrition_balance(self, nutrition, recommended):
        """
        영양 균형 평가
        """
        evaluation = {
            "overall": "보통",
            "suggestions": []
        }

        # 칼로리 평가
        if nutrition["calories"] < recommended["calories"] * 0.75:
            evaluation["overall"] = "부족"
            evaluation["suggestions"].append("칼로리 섭취가 부족합니다. 더 많은 음식을 섭취하세요.")
        elif nutrition["calories"] > recommended["calories"] * 1.25:
            evaluation["overall"] = "과다"
            evaluation["suggestions"].append("칼로리 섭취가 많습니다. 섭취량을 줄이세요.")

        # 단백질 평가
        if nutrition["protein"] < recommended["protein"] * 0.8:
            evaluation["suggestions"].append("단백질 섭취가 부족합니다. 고단백 식품을 추가하세요.")
        elif nutrition["protein"] > recommended["protein"] * 2:
            evaluation["suggestions"].append("단백질 섭취가 과다합니다. 섭취량을 조절하세요.")

        # 지방 평가
        if nutrition["fat"] < recommended["fat"] * 0.5:
            evaluation["suggestions"].append("지방 섭취가 부족합니다. 건강한 지방 섭취를 늘리세요.")
        elif nutrition["fat"] > recommended["fat"] * 1.5:
            evaluation["suggestions"].append("지방 섭취가 과다합니다. 섭취량을 줄이세요.")

        # 탄수화물 평가
        if nutrition["carbs"] < recommended["carbs"] * 0.7:
            evaluation["suggestions"].append("탄수화물 섭취가 부족합니다. 에너지 공급을 늘리세요.")
        elif nutrition["carbs"] > recommended["carbs"] * 1.3:
            evaluation["suggestions"].append("탄수화물 섭취가 과다합니다. 섭취량을 조절하세요.")

        # 나트륨 평가
        if "sodium" in nutrition and "sodium" in recommended:
            if nutrition["sodium"] > recommended["sodium"] * 1.3:
                evaluation["suggestions"].append("나트륨 섭취가 과다합니다. 가공식품과 소금 섭취를 줄이세요.")

        # 섬유질 평가
        if "fiber" in nutrition and "fiber" in recommended:
            if nutrition["fiber"] < recommended["fiber"] * 0.7:
                evaluation["suggestions"].append("섬유질 섭취가 부족합니다. 채소, 과일, 통곡물을 더 섭취하세요.")

        # 당류 평가
        if "sugar" in nutrition and "sugar" in recommended:
            if nutrition["sugar"] > recommended["sugar"] * 1.2:
                evaluation["suggestions"].append("당류 섭취가 과다합니다. 가공식품과 단 음식 섭취를 줄이세요.")

        return evaluation