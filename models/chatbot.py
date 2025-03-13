from app.extensions import db
from datetime import datetime

class Chatbot(db.Model):
    """챗봇 대화 모델"""
    __tablename__ = 'chatbot'

    cid = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.Integer, db.ForeignKey('users.uid'), nullable=False)
    query = db.Column(db.Text, nullable=False)  # 사용자 질문
    response = db.Column(db.Text, nullable=True)  # 챗봇 응답
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now)
    context = db.Column(db.Text, nullable=True)  # 대화 컨텍스트 (선택)

    def __init__(self, uid, query, response=None, context=None):
        """챗봇 대화 모델 초기화"""
        self.uid = uid
        self.query = query
        self.response = response
        self.timestamp = datetime.now()
        self.context = context

    def to_dict(self):
        """챗봇 대화 정보를 딕셔너리로 변환"""
        data = {
            'cid': self.cid,
            'uid': self.uid,
            'query': self.query,
            'response': self.response,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }

        # 컨텍스트가 있는 경우 JSON 파싱 시도
        if self.context:
            try:
                import json
                context_json = json.loads(self.context)
                data['context'] = context_json
            except json.JSONDecodeError:
                data['context'] = self.context

        return data

    def __repr__(self):
        """모델 표현"""
        return f'<Chatbot {self.cid}: {self.query[:20]}...>'