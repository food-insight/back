from app.extensions import db
from models.meal import Meal
from models.food import Food
from datetime import datetime

class MealService:
    def add_meal_record(self, user_id, data):
        """
        새로운 식사 기록 추가

        Args:
            user_id (int): 사용자 ID
            data (dict): 식사 기록 데이터

        Returns:
            dict: 작업 결과
        """
        try:
            # 식사 기록 생성
            meal = Meal(
                uid=user_id,
                meal_time=data.get('meal_time'),
                content=data.get('content'),
                date=datetime.strptime(data.get('date'), '%Y-%m-%d').date() if data.get('date') else datetime.now().date()
            )
            db.session.add(meal)
            db.session.flush()  # mid를 얻기 위해 flush

            # 음식 항목 추가
            food_names = data.get('food_names', [])
            for food_name in food_names:
                food = Food(
                    mid=meal.mid,
                    food_name=food_name
                )
                db.session.add(food)

            db.session.commit()

            return {
                'success': True,
                'meal_id': meal.mid,
                'message': '식사 기록이 성공적으로 저장되었습니다.'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }

    def get_user_meals(self, user_id, start_date=None, end_date=None,
                       meal_type=None, page=1, limit=10,
                       sort_by='datetime', sort_order='desc'):
        """
        사용자의 식사 기록 조회

        Args:
            user_id (int): 사용자 ID
            start_date (str, optional): 시작 날짜
            end_date (str, optional): 종료 날짜
            meal_type (str, optional): 식사 유형
            page (int): 페이지 번호
            limit (int): 페이지당 항목 수
            sort_by (str): 정렬 기준
            sort_order (str): 정렬 순서

        Returns:
            dict: 식사 기록 목록과 총 개수
        """
        try:
            query = Meal.query.filter_by(uid=user_id)

            # 날짜 필터링
            if start_date:
                query = query.filter(Meal.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
            if end_date:
                query = query.filter(Meal.date <= datetime.strptime(end_date, '%Y-%m-%d').date())

            # 식사 유형 필터링
            if meal_type:
                query = query.filter(Meal.meal_time == meal_type)

            # 정렬
            if sort_by == 'datetime':
                order_by = Meal.created_at.desc() if sort_order == 'desc' else Meal.created_at.asc()
            elif sort_by == 'date':
                order_by = Meal.date.desc() if sort_order == 'desc' else Meal.date.asc()
            else:
                order_by = Meal.created_at.desc()

            query = query.order_by(order_by)

            # 페이징
            total = query.count()
            meals = query.paginate(page=page, per_page=limit, error_out=False)

            return {
                'success': True,
                'meals': [meal.to_dict() for meal in meals.items],
                'total': total,
                'page': page,
                'limit': limit
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }