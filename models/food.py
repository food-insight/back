from app.extensions import db
import json
from datetime import datetime

class Food(db.Model):
    """음식 모델"""
    __tablename__ = 'food'

    fid = db.Column(db.Integer, primary_key=True)
    mid = db.Column(db.Integer, db.ForeignKey('meal.mid'), nullable=False)
    food_name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    calories = db.Column(db.Float, nullable=True)
    nutrition_info = db.Column(db.Text, nullable=True)  # JSON 형식으로 저장된 영양 정보
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 관계 설정
    allergies = db.relationship('Allergy', backref='food', lazy=True)
    recommendations = db.relationship('Recommendation', backref='food', lazy=True)

    def __init__(self, mid, food_name, category=None, calories=None, nutrition_info=None):
        """음식 모델 초기화"""
        self.mid = mid
        self.food_name = food_name
        self.category = category
        self.calories = calories

        # nutrition_info가 딕셔너리인 경우 JSON 문자열로 변환
        if nutrition_info:
            if isinstance(nutrition_info, dict):
                self.nutrition_info = json.dumps(nutrition_info)
            else:
                self.nutrition_info = nutrition_info

    def get_nutrition_info(self):
        """영양 정보를 딕셔너리로 반환"""
        if self.nutrition_info:
            try:
                return json.loads(self.nutrition_info)
            except json.JSONDecodeError:
                return {}
        return {}

    def update_nutrition_info(self, nutrition_data):
        """영양 정보 업데이트"""
        if nutrition_data:
            self.nutrition_info = json.dumps(nutrition_data)

            # 칼로리 정보가 있으면 칼로리 필드도 업데이트
            if 'calories' in nutrition_data:
                self.calories = nutrition_data['calories']

    def to_dict(self):
        """음식 정보를 딕셔너리로 변환"""
        return {
            'fid': self.fid,
            'mid': self.mid,
            'food_name': self.food_name,
            'category': self.category,
            'calories': self.calories,
            'nutrition_info': self.get_nutrition_info(),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }

    def __repr__(self):
        """모델 표현"""
        return f'<Food {self.fid}: {self.food_name}>'