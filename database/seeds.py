from app.extensions import db
from models.user import User
from models.food import Food
from models.meal import Meal
from models.allergy import Allergy
from models.recommendation import Recommendation
from models.ragdata import RagData
from datetime import datetime, timedelta
import random
import json
import logging

logger = logging.getLogger(__name__)

def seed_users(count=5):
    """샘플 사용자 데이터 생성"""
    logger.info(f"사용자 {count}개 시드 데이터 생성 중...")

    users = []
    health_goals = [
        "체중 감량", "근육 증가", "균형 잡힌 식단",
        "저탄수화물 식단", "고단백 식단", "채식"
    ]

    for i in range(1, count + 1):
        user = User(
            email=f"user{i}@example.com",
            password=f"password{i}",
            name=f"사용자{i}",
            gender=i % 2,  # 0 또는 1
            birth=datetime(1990 + i, 1, 1).date(),
            allergies="땅콩" if i % 3 == 0 else None,
            health_goal=health_goals[i % len(health_goals)]
        )
        users.append(user)

    db.session.add_all(users)
    db.session.commit()

    logger.info(f"사용자 {len(users)}개 생성 완료")
    return users

def seed_meals(users, count_per_user=10):
    """샘플 식사 데이터 생성"""
    logger.info(f"사용자당 식사 {count_per_user}개 시드 데이터 생성 중...")

    meals = []
    meal_times = ["아침", "점심", "저녁", "간식"]

    for user in users:
        for i in range(count_per_user):
            # 최근 30일 내의 날짜
            date = (datetime.now() - timedelta(days=random.randint(0, 30))).date()

            meal = Meal(
                uid=user.uid,
                meal_time=random.choice(meal_times),
                content=f"{date.strftime('%Y-%m-%d')}의 {meal_times[i % len(meal_times)]} 식사",
                date=date
            )
            meals.append(meal)

    db.session.add_all(meals)
    db.session.commit()

    logger.info(f"식사 {len(meals)}개 생성 완료")
    return meals

def seed_foods(meals, count_per_meal=3):
    """샘플 음식 데이터 생성"""
    logger.info(f"식사당 음식 {count_per_meal}개 시드 데이터 생성 중...")

    foods = []
    food_data = [
        {"name": "쌀밥", "category": "주식", "calories": 300, "nutrition": {"carbs": 65, "protein": 5, "fat": 0.5}},
        {"name": "김치찌개", "category": "국/찌개", "calories": 250, "nutrition": {"carbs": 10, "protein": 15, "fat": 12}},
        {"name": "불고기", "category": "육류", "calories": 400, "nutrition": {"carbs": 10, "protein": 30, "fat": 25}},
        {"name": "된장찌개", "category": "국/찌개", "calories": 200, "nutrition": {"carbs": 8, "protein": 12, "fat": 10}},
        {"name": "계란말이", "category": "반찬", "calories": 150, "nutrition": {"carbs": 2, "protein": 12, "fat": 10}},
        {"name": "삼겹살", "category": "육류", "calories": 500, "nutrition": {"carbs": 0, "protein": 25, "fat": 42}},
        {"name": "김치", "category": "반찬", "calories": 30, "nutrition": {"carbs": 6, "protein": 1, "fat": 0.2}},
        {"name": "잡곡밥", "category": "주식", "calories": 280, "nutrition": {"carbs": 60, "protein": 6, "fat": 1}},
        {"name": "샐러드", "category": "반찬", "calories": 100, "nutrition": {"carbs": 10, "protein": 3, "fat": 5}},
        {"name": "치킨", "category": "육류", "calories": 450, "nutrition": {"carbs": 15, "protein": 35, "fat": 30}},
        {"name": "피자", "category": "패스트푸드", "calories": 600, "nutrition": {"carbs": 70, "protein": 25, "fat": 30}},
        {"name": "햄버거", "category": "패스트푸드", "calories": 550, "nutrition": {"carbs": 40, "protein": 25, "fat": 30}},
        {"name": "우동", "category": "면류", "calories": 400, "nutrition": {"carbs": 80, "protein": 10, "fat": 1}},
        {"name": "라면", "category": "면류", "calories": 500, "nutrition": {"carbs": 70, "protein": 10, "fat": 20}},
        {"name": "떡볶이", "category": "분식", "calories": 450, "nutrition": {"carbs": 80, "protein": 8, "fat": 12}}
    ]

    for meal in meals:
        # 랜덤 음식 선택 (중복 없이)
        selected_foods = random.sample(food_data, min(count_per_meal, len(food_data)))

        for food_info in selected_foods:
            food = Food(
                mid=meal.mid,
                food_name=food_info["name"],
                category=food_info["category"],
                calories=food_info["calories"],
                nutrition_info=json.dumps(food_info["nutrition"])
            )
            foods.append(food)

    db.session.add_all(foods)
    db.session.commit()

    logger.info(f"음식 {len(foods)}개 생성 완료")
    return foods

def seed_allergies(users):
    """샘플 알레르기 데이터 생성"""
    logger.info("알레르기 시드 데이터 생성 중...")

    allergies = []
    allergy_types = ["땅콩", "우유", "밀가루", "해산물", "견과류", "계란", "대두"]

    for user in users:
        # 약 30%의 사용자에게만 알레르기 정보 추가
        if random.random() < 0.3:
            # 1~3개의 알레르기 정보 추가
            num_allergies = random.randint(1, 3)
            selected_allergies = random.sample(allergy_types, min(num_allergies, len(allergy_types)))

            for allergy_name in selected_allergies:
                allergy = Allergy(
                    uid=user.uid,
                    allergy_name=allergy_name
                )
                allergies.append(allergy)

    db.session.add_all(allergies)
    db.session.commit()

    logger.info(f"알레르기 {len(allergies)}개 생성 완료")
    return allergies

def seed_recommendations(users, foods):
    """샘플 추천 데이터 생성"""
    logger.info("추천 시드 데이터 생성 중...")

    recommendations = []
    recommendation_reasons = [
        "건강한 대체 식품으로 추천합니다",
        "당신의 건강 목표에 적합합니다",
        "영양 균형을 맞추기 위해 필요합니다",
        "단백질 섭취량을 늘리기 위해 추천합니다",
        "칼로리 섭취를 낮추기 위한 대안입니다"
    ]

    for user in users:
        # 각 사용자에게 2~5개의 추천 생성
        num_recommendations = random.randint(2, 5)

        for _ in range(num_recommendations):
            food = random.choice(foods)
            reason = random.choice(recommendation_reasons)

            recommendation = Recommendation(
                uid=user.uid,
                fid=food.fid,
                reason=reason
            )
            recommendations.append(recommendation)

    db.session.add_all(recommendations)
    db.session.commit()

    logger.info(f"추천 {len(recommendations)}개 생성 완료")
    return recommendations

def seed_ragdata():
    """샘플 RAG 데이터 생성"""
    logger.info("RAG 데이터 시드 생성 중...")

    rag_data = []
    rag_sources = [
        "영양학 논문 데이터베이스",
        "공신력 있는 건강 정보 사이트",
        "의학 저널",
        "식품 영양 성분표",
        "건강 관련 연구 결과"
    ]

    # 예시 데이터 30개 생성
    for i in range(30):
        source = random.choice(rag_sources)
        content = f"식단과 영양에 관한 정보 {i+1}번: 건강한 식습관을 위해서는 다양한 영양소를 골고루 섭취하는 것이 중요합니다. "
        content += "특히 단백질, 탄수화물, 지방, 비타민, 미네랄을 적절한 비율로 섭취해야 합니다."

        metadata = {
            "category": random.choice(["영양", "건강", "다이어트", "식단계획"]),
            "keywords": ["건강", "영양", "식습관"],
            "importance": random.randint(1, 5)
        }

        ragdata = RagData(
            source=source,
            content=content,
            metadata=json.dumps(metadata)
        )
        rag_data.append(ragdata)

    db.session.add_all(rag_data)
    db.session.commit()

    logger.info(f"RAG 데이터 {len(rag_data)}개 생성 완료")
    return rag_data

def seed_all():
    """모든 시드 데이터 생성"""
    logger.info("데이터베이스 시드 데이터 생성 시작")

    try:
        # 기존 데이터 삭제
        db.session.query(Recommendation).delete()
        db.session.query(Allergy).delete()
        db.session.query(Food).delete()
        db.session.query(Meal).delete()
        db.session.query(RagData).delete()
        db.session.query(User).delete()
        db.session.commit()

        # 새 데이터 생성
        users = seed_users(10)
        meals = seed_meals(users)
        foods = seed_foods(meals)
        seed_allergies(users)
        seed_recommendations(users, foods)
        seed_ragdata()

        logger.info("모든 시드 데이터 생성 완료")
    except Exception as e:
        db.session.rollback()
        logger.error(f"시드 데이터 생성 중 오류 발생: {str(e)}")
        raise

if __name__ == "__main__":
    from app import create_app

    app = create_app()
    with app.app_context():
        seed_all()