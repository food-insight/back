from app.extensions import db
from datetime import datetime

class Recommendation(db.Model):
    """식단 추천 모델"""
    __tablename__ = 'recommendation'

    rid = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.Integer, db.ForeignKey('users.uid'), nullable=False)
    mid = db.Column(db.Integer, db.ForeignKey('meal.mid'), nullable=True)  # 특정 식사에 대한 추천
    fid = db.Column(db.Integer, db.ForeignKey('food.fid'), nullable=True)  # 추천 음식
    reason = db.Column(db.Text, nullable=True)  # 추천 이유
    content = db.Column(db.Text, nullable=True)  # 추천 내용 (레시피, 대체 식품 등)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, uid, reason=None, content=None, mid=None, fid=None):
        """추천 모델 초기화"""
        self.uid = uid
        self.mid = mid
        self.fid = fid
        self.reason = reason
        self.content = content

    def to_dict(self):
        """추천 정보를 딕셔너리로 변환"""
        data = {
            'rid': self.rid,
            'uid': self.uid,
            'mid': self.mid,
            'fid': self.fid,
            'reason': self.reason,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

        # 추천 내용이 있는 경우 JSON 파싱 시도
        if self.content:
            try:
                import json
                content_json = json.loads(self.content)
                data['content'] = content_json
            except json.JSONDecodeError:
                data['content'] = self.content

        return data

    def __repr__(self):
        """모델 표현"""
        return f'<Recommendation {self.rid}>'