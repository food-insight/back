from services.chatbot import MealRepository as BaseMealRepository
from datetime import datetime

class MealRepository(BaseMealRepository):
    def get_meals_by_date_range(self, user_id, start_date, end_date):
        """
        특정 기간 내 사용자의 식사 기록 조회

        Args:
            user_id (str): 사용자 ID
            start_date (datetime): 시작 날짜
            end_date (datetime): 종료 날짜

        Returns:
            List[Dict]: 식사 기록 목록
        """
        # get_user_meals 메서드 활용
        meals = self.get_user_meals(int(user_id), start_date.strftime('%Y-%m-%d'))

        # 날짜 필터링
        filtered_meals = [
            meal for meal in meals
            if start_date.date() <= datetime.strptime(meal['date'], '%Y-%m-%d').date() <= end_date.date()
        ]

        return filtered_meals

    def get_recent_meals(self, user_id, limit=3):
        """
        최근 식사 기록 조회

        Args:
            user_id (str): 사용자 ID
            limit (int): 조회할 최대 식사 기록 수

        Returns:
            List[Dict]: 최근 식사 기록 목록
        """
        # get_user_meals 메서드 활용
        meals = self.get_user_meals(int(user_id))
        return meals[:limit]

    def get_user_meals(self, user_id, date=None):
        """
        특정 사용자의 식사 정보 조회

        Args:
            user_id (int): 사용자의 고유 식별자
            date (str, optional): 특정 날짜의 식사 정보 조회

        Returns:
            list: 식사 정보 딕셔너리 목록
        """
        # 기존 구현 유지
        return [
            {
                'id': 1,
                'user_id': user_id,
                'meal_type': '아침',
                'food_name': '현미밥',
                'food_items': ['오믈렛', '토스트', '과일'],
                'date': date or '2024-03-18',
                'total_calories': 450,
                'total_protein': 25,
                'total_carbs': 40,
                'total_fat': 15
            },
            {
                'id': 2,
                'user_id': user_id,
                'meal_type': '점심',
                'food_name': '닭가슴살',
                'food_items': ['닭가슴살 샐러드', '현미', '채소'],
                'date': date or '2024-03-18',
                'total_calories': 350,
                'total_protein': 35,
                'total_carbs': 30,
                'total_fat': 10
            }
        ]

    def log_meal(self, user_id, meal_data):
        """
        사용자의 새로운 식사 기록

        Args:
            user_id (int): 사용자의 고유 식별자
            meal_data (dict): 기록할 식사 정보

        Returns:
            bool: 식사 기록 성공 시 True, 실패 시 False
        """
        # 기존 구현 유지
        return True