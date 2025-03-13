from database.repositories.base_repository import BaseRepository
from models.food import Food
from app.extensions import db
from typing import Optional, List, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
import logging
import json

logger = logging.getLogger(__name__)

class FoodRepository(BaseRepository[Food]):
    """음식 저장소 클래스"""

    def __init__(self):
        """음식 저장소 초기화"""
        super().__init__(Food)

    def create_food(self, mid: int, food_name: str, category: Optional[str] = None,
                    calories: Optional[float] = None, nutrition_info: Optional[Dict] = None) -> Food:
        """
        음식 생성

        Args:
            mid (int): 식사 ID
            food_name (str): 음식 이름
            category (Optional[str]): 음식 카테고리
            calories (Optional[float]): 칼로리
            nutrition_info (Optional[Dict]): 영양 정보

        Returns:
            Food: 생성된 음식
        """
        return self.create(
            mid=mid,
            food_name=food_name,
            category=category,
            calories=calories,
            nutrition_info=nutrition_info
        )

    def get_foods_by_meal(self, mid: int) -> List[Food]:
        """
        식사별 음식 목록 조회

        Args:
            mid (int): 식사 ID

        Returns:
            List[Food]: 음식 목록
        """
        return self.find_by(mid=mid)

    def search_foods(self, keyword: str) -> List[Food]:
        """
        음식 검색

        Args:
            keyword (str): 검색어

        Returns:
            List[Food]: 음식 목록
        """
        try:
            return Food.query.filter(Food.food_name.like(f'%{keyword}%')).all()
        except SQLAlchemyError as e:
            logger.error(f"음식 검색 오류: {str(e)}")
            db.session.rollback()
            raise

    def get_foods_by_category(self, category: str) -> List[Food]:
        """
        카테고리별 음식 목록 조회

        Args:
            category (str): 카테고리

        Returns:
            List[Food]: 음식 목록
        """
        return self.find_by(category=category)

    def update_nutrition_info(self, food: Food, nutrition_data: Dict) -> Food:
        """
        음식 영양 정보 업데이트

        Args:
            food (Food): 업데이트할 음식
            nutrition_data (Dict): 영양 정보

        Returns:
            Food: 업데이트된 음식
        """
        try:
            # 영양 정보 JSON 변환
            if nutrition_data:
                nutrition_json = json.dumps(nutrition_data)

                # 칼로리 정보가 있으면 칼로리 필드도 업데이트
                calories = None
                if 'calories' in nutrition_data:
                    calories = float(nutrition_data['calories'])

                return self.update(food, nutrition_info=nutrition_json, calories=calories)
            return food
        except SQLAlchemyError as e:
            logger.error(f"음식 영양 정보 업데이트 오류: {str(e)}")
            db.session.rollback()
            raise

    def get_most_common_foods(self, uid: Optional[int] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        가장 자주 먹는 음식 목록 조회

        Args:
            uid (Optional[int]): 사용자 ID (없으면 전체)
            limit (int): 최대 개수

        Returns:
            List[Dict[str, Any]]: 음식 통계 목록
        """
        try:
            from models.meal import Meal

            query = db.session.query(
                Food.food_name,
                func.count(Food.fid).label('count')
            ).join(Meal)

            if uid:
                query = query.filter(Meal.uid == uid)

            result = query.group_by(Food.food_name) \
                .order_by(func.count(Food.fid).desc()) \
                .limit(limit) \
                .all()

            return [{'food_name': food_name, 'count': count} for food_name, count in result]
        except SQLAlchemyError as e:
            logger.error(f"가장 자주 먹는 음식 목록 조회 오류: {str(e)}")
            db.session.rollback()
            raise

    def get_average_calories_by_category(self, uid: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        카테고리별 평균 칼로리 조회

        Args:
            uid (Optional[int]): 사용자 ID (없으면 전체)

        Returns:
            List[Dict[str, Any]]: 카테고리별 평균 칼로리
        """
        try:
            from models.meal import Meal

            query = db.session.query(
                Food.category,
                func.avg(Food.calories).label('avg_calories'),
                func.count(Food.fid).label('count')
            ).join(Meal)

            if uid:
                query = query.filter(Meal.uid == uid)

            result = query.filter(Food.category.isnot(None)) \
                .filter(Food.calories.isnot(None)) \
                .group_by(Food.category) \
                .order_by(func.avg(Food.calories).desc()) \
                .all()

            return [{
                'category': category,
                'avg_calories': float(avg_calories) if avg_calories is not None else 0,
                'count': count
            } for category, avg_calories, count in result]
        except SQLAlchemyError as e:
            logger.error(f"카테고리별 평균 칼로리 조회 오류: {str(e)}")
            db.session.rollback()
            raise

    def get_nutrition_stats(self, uid: Optional[int] = None) -> Dict[str, Any]:
        """
        영양 통계 조회

        Args:
            uid (Optional[int]): 사용자 ID (없으면 전체)

        Returns:
            Dict[str, Any]: 영양 통계
        """
        try:
            from models.meal import Meal

            foods = []
            query = Food.query.join(Meal)

            if uid:
                query = query.filter(Meal.uid == uid)

            foods = query.all()

            # 영양소별 통계
            nutrition_sums = {}
            food_count = 0

            for food in foods:
                food_count += 1
                nutrition_info = food.get_nutrition_info()

                for key, value in nutrition_info.items():
                    if isinstance(value, (int, float)):
                        nutrition_sums[key] = nutrition_sums.get(key, 0) + value

            # 평균 계산
            nutrition_avg = {}
            if food_count > 0:
                for key, value in nutrition_sums.items():
                    nutrition_avg[key] = value / food_count

            return {
                'total': nutrition_sums,
                'average': nutrition_avg,
                'food_count': food_count
            }
        except SQLAlchemyError as e:
            logger.error(f"영양 통계 조회 오류: {str(e)}")
            db.session.rollback()
            raise