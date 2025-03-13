import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

class UserNutritionService:
    """
    사용자 맞춤형 영양 관리 서비스
    """
    def __init__(
            self,
            user_repository,
            meal_repository,
            nutrition_service,
            recommendation_service
    ):
        """
        사용자 영양 서비스 초기화

        Args:
            user_repository: 사용자 정보 저장소
            meal_repository: 식사 기록 저장소
            nutrition_service: 영양 분석 서비스
            recommendation_service: 추천 서비스
        """
        self.logger = logging.getLogger(__name__)
        self.user_repository = user_repository
        self.meal_repository = meal_repository
        self.nutrition_service = nutrition_service
        self.recommendation_service = recommendation_service

    def track_health_goal_progress(self, user_id: str) -> Dict[str, Any]:
        """
        사용자의 건강 목표 진행 상황 추적

        Args:
            user_id (str): 사용자 ID

        Returns:
            Dict[str, Any]: 건강 목표 진행 상황
        """
        try:
            # 사용자 정보 조회
            user = self.user_repository.get_user(user_id)

            # 최근 30일 식사 기록 조회
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            recent_meals = self.meal_repository.get_meals_by_date_range(
                user_id, start_date, end_date
            )

            # 일일 영양 분석
            daily_nutrition = self.nutrition_service.calculate_daily_nutrition(recent_meals)

            # 건강 목표별 진행 상황 평가
            goal_progress = self._evaluate_goal_progress(user, daily_nutrition)

            return {
                "user_id": user_id,
                "health_goal": user.health_goal,
                "daily_nutrition": daily_nutrition,
                "goal_progress": goal_progress
            }

        except Exception as e:
            self.logger.error(f"건강 목표 진행 상황 추적 중 오류: {str(e)}")
            return {}

    def _evaluate_goal_progress(
            self,
            user: Any,
            daily_nutrition: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        건강 목표별 진행 상황 평가

        Args:
            user (Any): 사용자 정보
            daily_nutrition (Dict[str, float]): 일일 영양 데이터

        Returns:
            Dict[str, Any]: 목표 진행 상황 평가
        """
        goal_progress = {
            "status": "보통",
            "recommendations": []
        }

        # 건강 목표별 평가 로직
        if user.health_goal == "체중 감량":
            # 칼로리 섭취량 평가
            if daily_nutrition.get("calories", 0) > 2000:
                goal_progress["status"] = "주의"
                goal_progress["recommendations"].append("일일 칼로리 섭취를 줄이세요.")

            # 탄수화물, 지방 섭취 평가
            if daily_nutrition.get("carbs", 0) > 200:
                goal_progress["recommendations"].append("탄수화물 섭취를 줄이세요.")

        elif user.health_goal == "근육 증가":
            # 단백질 섭취량 평가
            if daily_nutrition.get("protein", 0) < 1.6 * user.weight:
                goal_progress["status"] = "개선 필요"
                goal_progress["recommendations"].append("단백질 섭취를 늘리세요.")

            # 칼로리 섭취 평가
            if daily_nutrition.get("calories", 0) < 2500:
                goal_progress["recommendations"].append("충분한 칼로리를 섭취하세요.")

        elif user.health_goal == "당뇨 관리":
            # 탄수화물 섭취 평가
            if daily_nutrition.get("carbs", 0) > 150:
                goal_progress["status"] = "주의"
                goal_progress["recommendations"].append("탄수화물 섭취를 엄격히 관리하세요.")

            # 당 섭취 평가
            if daily_nutrition.get("sugar", 0) > 30:
                goal_progress["recommendations"].append("당 섭취를 줄이세요.")

        elif user.health_goal == "고혈압 관리":
            # 나트륨 섭취 평가
            if daily_nutrition.get("sodium", 0) > 1500:
                goal_progress["status"] = "주의"
                goal_progress["recommendations"].append("나트륨 섭취를 줄이세요.")

        return goal_progress

    def generate_personalized_recommendations(self, user_id: str) -> Dict[str, Any]:
        """
        개인화된 영양 및 식단 추천

        Args:
            user_id (str): 사용자 ID

        Returns:
            Dict[str, Any]: 개인화된 추천
        """
        try:
            # 사용자 정보 조회
            user = self.user_repository.get_user(user_id)

            # 최근 섭취 음식 조회
            recent_meals = self.meal_repository.get_recent_meals(user_id, limit=7)
            recent_foods = [meal.food_name for meal in recent_meals]

            # 알레르기 정보 조회
            allergies = self.user_repository.get_user_allergies(user_id)

            # 맞춤형 식단 추천
            meal_recommendations = self.recommendation_service.generate_meal_recommendations(
                user=user,
                allergies=allergies,
                recent_foods=recent_foods
            )

            # 대체 음식 추천
            alternative_foods = {}
            for category, recommendations in meal_recommendations.items():
                alternative_foods[category] = [
                    self.recommendation_service.generate_food_alternatives(
                        food['name'],
                        reason=user.health_goal,
                        allergies=allergies
                    ) for food in recommendations
                ]

            return {
                "meal_recommendations": meal_recommendations,
                "alternative_foods": alternative_foods
            }

        except Exception as e:
            self.logger.error(f"개인화된 추천 생성 중 오류: {str(e)}")
            return {}

def initialize_user_nutrition_service(
        user_repository,
        meal_repository,
        nutrition_service,
        recommendation_service
) -> UserNutritionService:
    """
    사용자 영양 서비스 초기화

    Args:
        user_repository: 사용자 정보 저장소
        meal_repository: 식사 기록 저장소
        nutrition_service: 영양 분석 서비스
        recommendation_service: 추천 서비스

    Returns:
        UserNutritionService: 초기화된 사용자 영양 서비스
    """
    return UserNutritionService(
        user_repository=user_repository,
        meal_repository=meal_repository,
        nutrition_service=nutrition_service,
        recommendation_service=recommendation_service
    )