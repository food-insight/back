from app.extensions import db
from datetime import datetime

class RagData(db.Model):
    """RAG 데이터 모델 - 영양 정보 및 연구 데이터"""
    __tablename__ = 'ragdata'

    rid = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.Text, nullable=False)  # 데이터 출처
    content = db.Column(db.Text, nullable=False)  # 실제 콘텐츠
    metadata = db.Column(db.Text, nullable=True)  # 메타데이터 (JSON 형식)
    embedding = db.Column(db.Text, nullable=True)  # 벡터 임베딩 (JSON 형식)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __init__(self, source, content, metadata=None, embedding=None):
        """RAG 데이터 모델 초기화"""
        self.source = source
        self.content = content

        # 메타데이터가 딕셔너리인 경우 JSON 문자열로 변환
        if metadata:
            if isinstance(metadata, dict):
                import json
                self.metadata = json.dumps(metadata)
            else:
                self.metadata = metadata

        # 임베딩이 리스트/배열인 경우 JSON 문자열로 변환
        if embedding:
            if isinstance(embedding, (list, tuple)):
                import json
                self.embedding = json.dumps(embedding)
            else:
                self.embedding = embedding

    def get_metadata(self):
        """메타데이터를 딕셔너리로 반환"""
        if self.metadata:
            try:
                import json
                return json.loads(self.metadata)
            except json.JSONDecodeError:
                return {}
        return {}

    def get_embedding(self):
        """임베딩을 리스트로 반환"""
        if self.embedding:
            try:
                import json
                return json.loads(self.embedding)
            except json.JSONDecodeError:
                return []
        return []

    def to_dict(self):
        """RAG 데이터를 딕셔너리로 변환"""
        return {
            'rid': self.rid,
            'source': self.source,
            'content': self.content,
            'metadata': self.get_metadata(),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

    def __repr__(self):
        """모델 표현"""
        return f'<RagData {self.rid}: {self.source}>'