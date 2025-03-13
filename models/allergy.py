from app.extensions import db
from datetime import datetime

class Allergy(db.Model):
    """알레르기 모델"""
    __tablename__ = 'allergy'

    aid = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.Integer, db.ForeignKey('users.uid'), nullable=False)
    fid = db.Column(db.Integer, db.ForeignKey('food.fid'), nullable=True)  # 특정 음식과 연결 가능
    allergy_name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, uid, allergy_name, fid=None):
        """알레르기 모델 초기화"""
        self.uid = uid
        self.allergy_name = allergy_name
        self.fid = fid

    def to_dict(self):
        """알레르기 정보를 딕셔너리로 변환"""
        return {
            'aid': self.aid,
            'uid': self.uid,
            'fid': self.fid,
            'allergy_name': self.allergy_name,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }

    def __repr__(self):
        """모델 표현"""
        return f'<Allergy {self.aid}: {self.allergy_name}>'