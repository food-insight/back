from database.repositories.base_repository import BaseRepository
from models.meal import Meal
from models.food import Food
from app.extensions import db
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class MealRepository(BaseRepository[Meal]):
    """식사 저장소 클래스"""

    def __init__(self):
        """식사 저장소 초기화"""
        super().__init__(Meal)

    def create_meal(self, uid: int, meal_time: str, content: Optional[str] = None,
                    image: Optional[bytes] = None, image_path: Optional[str] = None,
                    date: Optional[datetime] = None) -> Meal:
        """
        식사 기록 생성

        Args:
            uid (int): 사용자 ID
            meal_time (str): 식사 시간 (아침, 점심, 저녁, 간식 등)
            content (Optional[str]): 식사 설명
            image (Optional[bytes]): 식사 이미지 바이너리 데이터
            image_path (Optional[str]): 이미지 파일 경로
            date (Optional[datetime]): 식사 날짜

        Returns:
            Meal: 생성된 식사 기록
        """
        return self.create(
            uid=uid,
            meal_time=meal_time,
            content=content,
            image=image,
            image_path=image_path,
            date=date or datetime.now().date()
        )

    def get_user_meals(self, uid: int, start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None, meal_time: Optional[str] = None,
                       page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        사용자 식사 기록 조회

        Args:
            uid (int): 사용자 ID
            start_date (Optional[datetime]): 시작 날짜
            end_date (Optional[datetime]): 종료 날짜
            meal_time (Optional[str]): 식사 시간
            page (int): 페이지 번호
            per_page (int): 페이지당 항목 수

        Returns:
            Dict[str, Any]: 페이지네이션 결과
        """
        try:
            query = Meal.query.filter_by(uid=uid)

            if start_date:
                query = query.filter(Meal.date >= start_date)

            if end_date:
                query = query.filter(Meal.date <= end_date)

            if meal_time:
                query = query.filter_by(meal_time=meal_time)

            query = query.order_by(Meal.date.desc(), Meal.mid.desc())

            total = query.count()
            items = query.offset((page - 1) * per_page).limit(per_page).all()

            return {
                'items': items,
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page,
                'has_next': page < ((total + per_page - 1) // per_page),
                'has_prev': page > 1
            }
        except SQLAlchemyError as e:
            logger.error(f"사용자 식사 기록 조회 오류: {str(e)}")
            db.session.rollback()
            raise

    def get_today_meals(self, uid: int) -> List[Meal]:
        """
        오늘 식사 기록 조회

        Args:
            uid (int): 사용자 ID

        Returns:
            List[Meal]: 식사 기록 목록
        """
        today = datetime.now().date()
        return self.find_by(uid=uid, date=today)

    def get_weekly_meals(self, uid: int) -> Tuple[List[Meal], datetime, datetime]:
        """
        주간 식사 기록 조회

        Args:
            uid (int): 사용자 ID

        Returns:
            Tuple[List[Meal], datetime, datetime]: 식사 기록 목록, 시작 날짜, 종료 날짜
        """
        today = datetime.now().date()
        start_date = today - timedelta(days=6)  # 7일간의 데이터

        try:
            meals = Meal.query.filter(
                Meal.uid == uid,
                Meal.date >= start_date,
                Meal.date <= today
            ).order_by(Meal.date).all()

            return meals, start_date, today
        except SQLAlchemyError as e:
            logger.error(f"주간 식사 기록 조회 오류: {str(e)}")
            db.session.rollback()
            raise

    def add_food_to_meal(self, meal_id: int, food_name: str, category: Optional[str] = None,
                         calories: Optional[float] = None, nutrition_info: Optional[Dict] = None) -> Food:
        """
        식사에 음식 추가

        Args:
            meal_id (int): 식사 ID
            food_name (str): 음식 이름
            category (Optional[str]): 음식 카테고리
            calories (Optional[float]): 칼로리
            nutrition_info (Optional[Dict]): 영양 정보

        Returns:
            Food: 추가된 음식
        """
        try:
            food = Food(
                mid=meal_id,
                food_name=food_name,
                category=category,
                calories=calories,
                nutrition_info=nutrition_info
            )

            db.session.add(food)
            db.session.commit()
            return food
        except SQLAlchemyError as e:
            logger.error(f"식사에 음식 추가 오류: {str(e)}")
            db.session.rollback()
            raise

    def get_meal_stats(self, uid: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        식사 통계 계산

        Args:
            uid (int): 사용자 ID
            start_date (datetime): 시작 날짜
            end_date (datetime): 종료 날짜

        Returns:
            Dict[str, Any]: 통계 정보
        """
        try:
            meals = Meal.query.filter(
                Meal.uid == uid,
                Meal.date >= start_date,
                Meal.date <= end_date
            ).all()

            # 식사 시간별 통계
            meal_time_stats = {}
            for meal in meals:
                meal_time_stats[meal.meal_time] = meal_time_stats.get(meal.meal_time, 0) + 1

            # 날짜별 식사 수
            date_stats = {}
            for meal in meals:
                date_str = meal.date.strftime('%Y-%m-%d')
                date_stats[date_str] = date_stats.get(date_str, 0) + 1

            # 식사별 음식 통계
            food_stats = {}
            for meal in meals:
                for food in meal.foods:
                    food_stats[food.food_name] = food_stats.get(food.food_name, 0) + 1

            # 가장 자주 먹는 음식 Top 5
            top_foods = sorted(food_stats.items(), key=lambda x: x[1], reverse=True)[:5]

            return {
                'meal_time_stats': meal_time_stats,
                'date_stats': date_stats,
                'top_foods': [{'name': name, 'count': count} for name, count in top_foods],
                'total_meals': len(meals)
            }
        except SQLAlchemyError as e:
            logger.error(f"식사 통계 계산 오류: {str(e)}")
            raise