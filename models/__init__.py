# models/__init__.py
# 모든 모델 클래스를 여기에서 가져옵니다.
# 이렇게 하면 순환 참조 문제를 방지하고 모든 모델이 적절히 초기화됩니다.

from app.extensions import db

# 모든 모델 클래스를 임포트
from models.user import User
from models.chatbot import Chatbot