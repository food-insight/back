from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model):
    """사용자 모델"""
    __tablename__ = 'users'

    uid = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.Integer, nullable=True)  # 0: 남성, 1: 여성, Null: 기타
    birth = db.Column(db.Date, nullable=True)
    allergies = db.Column(db.Text, nullable=True)  # 알레르기 정보 (텍스트 형식)
    health_goal = db.Column(db.Text, nullable=True)  # 건강 목표
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 관계 설정 (관계형 데이터베이스 연결)
    meals = db.relationship('Meal', backref='user', lazy=True, cascade='all, delete-orphan')
    allergies_rel = db.relationship('Allergy', backref='user', lazy=True, cascade='all, delete-orphan')
    recommendations = db.relationship('Recommendation', backref='user', lazy=True, cascade='all, delete-orphan')
    chatbot_queries = db.relationship('Chatbot', backref='user', lazy=True, cascade='all, delete-orphan')

    def __init__(self, email, password, name, gender=None, birth=None, allergies=None, health_goal=None):
        """사용자 모델 초기화"""
        self.email = email
        self.password = generate_password_hash(password)
        self.name = name
        self.gender = gender
        self.birth = birth
        self.allergies = allergies
        self.health_goal = health_goal

    def check_password(self, password):
        """비밀번호 확인"""
        return check_password_hash(self.password, password)

    def update_password(self, password):
        """비밀번호 업데이트"""
        self.password = generate_password_hash(password)

    def calculate_age(self):
        """나이 계산"""
        if self.birth:
            today = datetime.now().date()
            return today.year - self.birth.year - ((today.month, today.day) < (self.birth.month, self.birth.day))
        return None

    def to_dict(self):
        """사용자 정보를 딕셔너리로 변환"""
        return {
            'uid': self.uid,
            'email': self.email,
            'name': self.name,
            'gender': self.gender,
            'birth': self.birth.strftime('%Y-%m-%d') if self.birth else None,
            'allergies': self.allergies,
            'health_goal': self.health_goal,
            'age': self.calculate_age(),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }

    def __repr__(self):
        """모델 표현"""
        return f'<User {self.email}>'