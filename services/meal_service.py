from app.extensions import db
from models.meal import Meal
from models.food import Food
from datetime import datetime

class MealService:
    def add_meal_record(self, user_id, data):
        """
        새로운 식사 기록 추가
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

    def get_meal_detail(self, meal_id, user_id):
        """
        특정 식사 기록을 조회하는 메서드
        """
        try:
            meal = Meal.query.filter_by(mid=meal_id, uid=user_id).first()

            if not meal:
                return {"success": False, "error": "해당 식사 기록을 찾을 수 없습니다."}

            # 해당 식사에 포함된 음식 조회
            foods = Food.query.filter_by(mid=meal.mid).all()
            food_names = [food.food_name for food in foods]

            return {
                "success": True,
                "meal": {
                    "meal_id": meal.mid,
                    "meal_time": meal.meal_time,
                    "content": meal.content,
                    "foods": food_names,
                    "created_at": meal.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_meal_record(self, meal_id, user_id, data):
        """
        특정 식사 기록을 수정하는 메서드
        """
        try:
            meal = Meal.query.filter_by(mid=meal_id, uid=user_id).first()

            if not meal:
                return {"success": False, "error": "해당 식사 기록을 찾을 수 없습니다."}

            # 요청 데이터에서 필드 업데이트
            if "meal_time" in data:
                meal.meal_time = data["meal_time"]
            if "content" in data:
                meal.content = data["content"]

            # 기존 음식 목록 삭제 후 새 음식 추가
            if "foods" in data:
                Food.query.filter_by(mid=meal_id).delete()
                for food_name in data["foods"]:
                    new_food = Food(mid=meal_id, food_name=food_name)
                    db.session.add(new_food)

            db.session.commit()  # DB 업데이트 적용

            return {"success": True, "message": "식사 기록이 성공적으로 수정되었습니다."}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
        
    def delete_meal_record(self, meal_id, user_id):
        """
        특정 식사 기록을 삭제하는 메서드
        """
        try:
            meal = Meal.query.filter_by(mid=meal_id, uid=user_id).first()

            if not meal:
                return {"success": False, "error": "해당 식사 기록을 찾을 수 없습니다."}

            # 해당 식사의 음식 데이터 삭제
            Food.query.filter_by(mid=meal_id).delete()

            # 식사 기록 삭제
            db.session.delete(meal)
            db.session.commit()

            return {"success": True, "message": "식사 기록이 성공적으로 삭제되었습니다."}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}

    def get_meal_statistics(self, user_id, start_date=None, end_date=None, group_by='day'):
        """
        사용자의 식사 통계를 조회하는 메서드
        """
        try:
            query = Meal.query.filter_by(uid=user_id)

            # 날짜 필터링
            if start_date:
                query = query.filter(Meal.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
            if end_date:
                query = query.filter(Meal.date <= datetime.strptime(end_date, '%Y-%m-%d').date())

            total_meals = query.count()
            total_calories = 0
            food_counts = {}

            meals = query.all()
            for meal in meals:
                foods = Food.query.filter_by(mid=meal.mid).all()
                for food in foods:
                    food_name = food.food_name
                    food_counts[food_name] = food_counts.get(food_name, 0) + 1
                    if food.calories:
                        total_calories += food.calories

            # 그룹화 옵션 처리 (날짜별, 주별, 월별)
            grouped_stats = {}
            for meal in meals:
                if group_by == 'day':
                    key = meal.date.strftime('%Y-%m-%d')
                elif group_by == 'week':
                    key = meal.date.strftime('%Y-%W')  # 주 단위
                elif group_by == 'month':
                    key = meal.date.strftime('%Y-%m')  # 월 단위
                else:
                    key = 'unknown'

                if key not in grouped_stats:
                    grouped_stats[key] = {'meals': 0, 'calories': 0}

                grouped_stats[key]['meals'] += 1
                grouped_stats[key]['calories'] += sum(food.calories for food in foods if food.calories)

            return {
                "success": True,
                "total_meals": total_meals,
                "total_calories": total_calories,
                "most_frequent_foods": dict(sorted(food_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
                "grouped_statistics": grouped_stats
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
