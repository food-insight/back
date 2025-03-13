from flask import current_app
from datetime import datetime, timedelta
import json

def calculate_daily_nutrition_target(user):
    """사용자별 일일 영양소 권장량 계산 헬퍼 함수"""
    if not user:
        # 기본값 반환
        return {
            'calories': 2000,
            'protein': 60,
            'carbs': 275,
            'fat': 65,
            'fiber': 25,
            'sugar': 50,
            'sodium': 2300
        }

    # 사용자 정보
    age = user.calculate_age() or 30  # 기본값 30
    gender = user.gender  # 0: 남성, 1: 여성

    # 건강 목표에 따라 조정
    health_goal = user.health_goal or ''

    # 기본 값 (성인 평균)
    base_targets = {
        'calories': 2000,
        'protein': 60,
        'carbs': 275,
        'fat': 65,
        'fiber': 25,
        'sugar': 50,
        'sodium': 2300
    }

    # 성별에 따른 조정
    if gender == 0:  # 남성
        base_targets['calories'] = 2500
        base_targets['protein'] = 70
        base_targets['carbs'] = 325
        base_targets['fat'] = 80
    elif gender == 1:  # 여성
        base_targets['calories'] = 2000
        base_targets['protein'] = 60
        base_targets['carbs'] = 275
        base_targets['fat'] = 65

    # 연령에 따른 조정
    if age <= 18:
        base_targets['calories'] += 300
        base_targets['protein'] += 10
    elif age >= 60:
        base_targets['calories'] -= 200
        base_targets['calcium'] = 1200  # 추가 영양소

    # 건강 목표에 따른 조정
    if '체중 감량' in health_goal or '다이어트' in health_goal:
        base_targets['calories'] *= 0.8
        base_targets['protein'] *= 1.2
        base_targets['carbs'] *= 0.7
        base_targets['fat'] *= 0.7
    elif '근육 증가' in health_goal or '벌크업' in health_goal:
        base_targets['calories'] *= 1.2
        base_targets['protein'] *= 1.5
        base_targets['carbs'] *= 1.2
    elif '당뇨' in health_goal:
        base_targets['carbs'] *= 0.7
        base_targets['sugar'] *= 0.5
    elif '고혈압' in health_goal:
        base_targets['sodium'] *= 0.6

    # 값 반올림
    for key in base_targets:
        base_targets[key] = round(base_targets[key])

    return base_targets

def generate_nutrition_insights(nutrition_data, user):
    """영양 데이터 기반 인사이트 생성 헬퍼 함수"""
    if not nutrition_data:
        return []

    # 사용자별 목표 영양소
    targets = calculate_daily_nutrition_target(user)

    insights = []

    # 칼로리 인사이트
    calories = nutrition_data.get('calories', 0)
    calories_target = targets['calories']
    calories_percentage = round(calories / calories_target * 100, 1) if calories_target > 0 else 0

    if calories_percentage > 110:
        insights.append({
            'type': 'warning',
            'title': '칼로리 과다 섭취',
            'content': f'목표 칼로리({calories_target}kcal)의 {calories_percentage}%를 섭취했습니다. 칼로리 섭취를 줄이는 것이 좋습니다.'
        })
    elif calories_percentage < 70:
        insights.append({
            'type': 'info',
            'title': '칼로리 부족',
            'content': f'목표 칼로리({calories_target}kcal)의 {calories_percentage}%만 섭취했습니다. 적절한 에너지 섭취를 위해 더 드셔도 됩니다.'
        })
    else:
        insights.append({
            'type': 'success',
            'title': '적절한 칼로리 섭취',
            'content': f'목표 칼로리({calories_target}kcal)의 {calories_percentage}%를 섭취했습니다. 균형 잡힌 섭취량입니다.'
        })

    # 단백질 인사이트
    protein = nutrition_data.get('protein', 0)
    protein_target = targets['protein']
    protein_percentage = round(protein / protein_target * 100, 1) if protein_target > 0 else 0

    if protein_percentage < 80:
        insights.append({
            'type': 'warning',
            'title': '단백질 부족',
            'content': f'목표 단백질({protein_target}g)의 {protein_percentage}%만 섭취했습니다. 단백질이 풍부한 식품을 더 섭취하세요.'
        })
    elif protein_percentage > 150:
        insights.append({
            'type': 'info',
            'title': '단백질 과다 섭취',
            'content': f'목표 단백질({protein_target}g)의 {protein_percentage}%를 섭취했습니다. 장기적으로는 적절한 양을 유지하는 것이 좋습니다.'
        })

    # 탄수화물 인사이트
    carbs = nutrition_data.get('carbs', 0)
    carbs_target = targets['carbs']
    carbs_percentage = round(carbs / carbs_target * 100, 1) if carbs_target > 0 else 0

    if carbs_percentage > 120:
        insights.append({
            'type': 'info',
            'title': '탄수화물 과다 섭취',
            'content': f'목표 탄수화물({carbs_target}g)의 {carbs_percentage}%를 섭취했습니다. 단순당 섭취를 줄이세요.'
        })

    # 지방 인사이트
    fat = nutrition_data.get('fat', 0)
    fat_target = targets['fat']
    fat_percentage = round(fat / fat_target * 100, 1) if fat_target > 0 else 0

    if fat_percentage > 120:
        insights.append({
            'type': 'warning',
            'title': '지방 과다 섭취',
            'content': f'목표 지방({fat_target}g)의 {fat_percentage}%를 섭취했습니다. 포화지방과 트랜스지방을 줄이세요.'
        })

    # 영양 균형 인사이트
    if 'carbs' in nutrition_data and 'protein' in nutrition_data and 'fat' in nutrition_data:
        total_macros = carbs + protein + fat
        if total_macros > 0:
            carbs_ratio = round(carbs / total_macros * 100)
            protein_ratio = round(protein / total_macros * 100)
            fat_ratio = round(fat / total_macros * 100)

            balanced = (40 <= carbs_ratio <= 60) and (15 <= protein_ratio <= 35) and (20 <= fat_ratio <= 35)

            if balanced:
                insights.append({
                    'type': 'success',
                    'title': '균형 잡힌 영양소 비율',
                    'content': f'탄수화물({carbs_ratio}%), 단백질({protein_ratio}%), 지방({fat_ratio}%)의 비율이 균형적입니다.'
                })
            else:
                insights.append({
                    'type': 'info',
                    'title': '영양소 비율 개선 필요',
                    'content': f'현재 탄수화물({carbs_ratio}%), 단백질({protein_ratio}%), 지방({fat_ratio}%)의 비율입니다. 권장 비율은 탄수화물(50%), 단백질(20%), 지방(30%) 입니다.'
                })

    # 섬유질 인사이트
    fiber = nutrition_data.get('fiber', 0)
    fiber_target = targets['fiber']

    if fiber < fiber_target * 0.7:
        insights.append({
            'type': 'warning',
            'title': '식이 섬유 부족',
            'content': f'식이 섬유 섭취량({fiber}g)이 목표({fiber_target}g)보다 부족합니다. 과일, 채소, 통곡물을 더 섭취하세요.'
        })

    # 나트륨 인사이트
    sodium = nutrition_data.get('sodium', 0)
    sodium_target = targets['sodium']

    if sodium > sodium_target:
        insights.append({
            'type': 'warning',
            'title': '나트륨 과다 섭취',
            'content': f'나트륨 섭취량({sodium}mg)이 권장량({sodium_target}mg)을 초과했습니다. 가공식품과 소금 섭취를 줄이세요.'
        })

    return insights

def format_nutrition_data(nutrition_data):
    """영양 데이터 포맷팅 헬퍼 함수"""
    if not nutrition_data:
        return {}

    # 주요 영양소 단위 정의
    units = {
        'calories': 'kcal',
        'protein': 'g',
        'carbs': 'g',
        'fat': 'g',
        'fiber': 'g',
        'sugar': 'g',
        'sodium': 'mg',
        'cholesterol': 'mg',
        'calcium': 'mg',
        'iron': 'mg',
        'vitamin_a': 'IU',
        'vitamin_c': 'mg',
        'vitamin_d': 'IU'
    }

    # 포맷팅된 데이터
    formatted_data = {}

    for key, value in nutrition_data.items():
        unit = units.get(key, '')
        formatted_value = round(value, 1) if isinstance(value, float) else value

        formatted_data[key] = {
            'value': formatted_value,
            'unit': unit,
            'display': f"{formatted_value}{unit}"
        }

    return formatted_data

def compare_nutrition_with_previous(current_data, previous_data):
    """현재 영양 데이터와 이전 데이터 비교 헬퍼 함수"""
    if not current_data or not previous_data:
        return {}

    comparison = {}

    for key in current_data:
        if key in previous_data:
            current_value = current_data[key]
            previous_value = previous_data[key]

            # 변화량과 퍼센트
            change = current_value - previous_value
            percentage = round((change / previous_value * 100), 1) if previous_value != 0 else 0

            comparison[key] = {
                'current': current_value,
                'previous': previous_value,
                'change': change,
                'percentage': percentage,
                'trend': 'up' if change > 0 else ('down' if change < 0 else 'same')
            }

    return comparison