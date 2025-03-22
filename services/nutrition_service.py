from services.chatbot import NutritionService as BaseNutritionService

class NutritionService(BaseNutritionService):
    def calculate_daily_nutrition(self, meals):
        """
        일일 영양 섭취량 계산
        
        Args:
            meals (List[Dict]): 식사 기록 목록
        
        Returns:
            Dict: 일일 영양 섭취량 정보
        """
        daily_nutrition = {
            'total_calories': 0,
            'total_protein': 0,
            'total_carbs': 0,
            'total_fat': 0
        }

        for meal in meals:
            daily_nutrition['total_calories'] += meal.get('total_calories', 0)
            daily_nutrition['total_protein'] += meal.get('total_protein', 0)
            daily_nutrition['total_carbs'] += meal.get('total_carbs', 0)
            daily_nutrition['total_fat'] += meal.get('total_fat', 0)

        return daily_nutrition

    def get_nutrition_insights(self, daily_nutrition, is_average=True):
        """
        영양 섭취 인사이트 생성
        
        Args:
            daily_nutrition (Dict): 일일 영양 섭취량
            is_average (bool): 평균 계산 여부
        
        Returns:
            Dict: 영양 섭취 인사이트
        """
        return {
            'total_calories': daily_nutrition['total_calories'],
            'insights': [
                f"총 칼로리: {daily_nutrition['total_calories']}kcal",
                f"단백질: {daily_nutrition['total_protein']}g",
                f"탄수화물: {daily_nutrition['total_carbs']}g",
                f"지방: {daily_nutrition['total_fat']}g"
            ]
        }

    def get_recipe_recommendations(self, health_goal: str):
        """
        건강 목표에 따른 레시피 추천
        
        Args:
            health_goal (str): 건강 목표
        
        Returns:
            Dict: 레시피 추천 정보
        """
        # 기존 구현 유지
        recommendations = {
            '체중 감량': [
                {'name': '그릴드 닭가슴살 샐러드', 'calories': 300},
                {'name': '두부 현미밥', 'calories': 250}
            ],
            '근육 증가': [
                {'name': '연어 퀴노아 볼', 'calories': 450},
                {'name': '단백질 스무디', 'calories': 350}
            ],
            '당뇨 관리': [
                {'name': '통곡물 아침 오트밀', 'calories': 280},
                {'name': '저당 채소 스프', 'calories': 200}
            ]
        }

        return {
            'recipes': recommendations.get(health_goal, [])
        }

    def get_food_nutrition(self, food_name: str):
        """
        특정 음식의 영양 정보 조회
        
        Args:
            food_name (str): 음식 이름
        
        Returns:
            Dict: 음식 영양 정보
        """
        # 기존 구현 유지
        food_nutrition = {
            '현미밥': {'calories': 150, 'protein': 3, 'carbohydrates': 30, 'fat': 1},
            '닭가슴살': {'calories': 120, 'protein': 26, 'carbohydrates': 0, 'fat': 3},
            '브로콜리': {'calories': 55, 'protein': 4, 'carbohydrates': 11, 'fat': 0.6}
        }

        return food_nutrition.get(food_name, {
            'calories': 0,
            'protein': 0,
            'carbohydrates': 0,
            'fat': 0
        })
    
        