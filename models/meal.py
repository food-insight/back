from app.extensions import db
from datetime import datetime

class Meal(db.Model):
    """식사 모델"""
    __tablename__ = 'meal'

    mid = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.Integer, db.ForeignKey('users.uid'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.now().date())
    meal_time = db.Column(db.String(50), nullable=False)  # 아침, 점심, 저녁, 간식 등
    content = db.Column(db.Text, nullable=True)  # 식사 설명
    image = db.Column(db.BLOB, nullable=True)  # 식사 이미지 (바이너리 데이터)
    image_path = db.Column(db.String(255), nullable=True)  # 이미지 파일 경로 (대안)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 관계 설정
    foods = db.relationship('Food', backref='meal', lazy=True, cascade='all, delete-orphan')
    recommendations = db.relationship('Recommendation', backref='meal', lazy=True, cascade='all, delete-orphan')

    def __init__(self, uid, meal_time, content=None, image=None, image_path=None, date=None):
        """식사 모델 초기화"""
        self.uid = uid
        self.meal_time = meal_time
        self.content = content
        self.image = image
        self.image_path = image_path
        self.date = date if date else datetime.now().date()

    def to_dict(self):
        """식사 정보를 딕셔너리로 변환"""
        return {
            'mid': self.mid,
            'uid': self.uid,
            'date': self.date.strftime('%Y-%m-%d'),
            'meal_time': self.meal_time,
            'content': self.content,
            'has_image': True if self.image or self.image_path else False,
            'image_path': self.image_path,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'foods': [food.to_dict() for food in self.foods]
        }

    def get_total_calories(self):
        """식사의 총 칼로리 계산"""
        total = 0
        for food in self.foods:
            if food.calories:
                total += food.calories
        return total

    def __repr__(self):
        """모델 표현"""
        return f'<Meal {self.mid}: {self.date} {self.meal_time}>'