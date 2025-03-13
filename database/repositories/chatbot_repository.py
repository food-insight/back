from database.repositories.base_repository import BaseRepository
from models.chatbot import Chatbot
from app.extensions import db
from typing import Optional, List, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)

class ChatbotRepository(BaseRepository[Chatbot]):
    """챗봇 저장소 클래스"""

    def __init__(self):
        """챗봇 저장소 초기화"""
        super().__init__(Chatbot)

    def create_conversation(self, uid: int, query: str, response: Optional[str] = None,
                            context: Optional[Dict] = None) -> Chatbot:
        """
        대화 생성

        Args:
            uid (int): 사용자 ID
            query (str): 사용자 질문
            response (Optional[str]): 챗봇 응답
            context (Optional[Dict]): 대화 컨텍스트

        Returns:
            Chatbot: 생성된 대화
        """
        context_str = None
        if context:
            context_str = json.dumps(context)

        return self.create(
            uid=uid,
            query=query,
            response=response,
            context=context_str
        )

    def get_user_conversation_history(self, uid: int, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """
        사용자 대화 기록 페이지네이션

        Args:
            uid (int): 사용자 ID
            page (int): 페이지 번호
            per_page (int): 페이지당 항목 수

        Returns:
            Dict[str, Any]: 페이지네이션 결과
        """
        try:
            query = Chatbot.query.filter_by(uid=uid).order_by(Chatbot.timestamp.desc())

            total = query.count()
            items = query.offset((page - 1) * per_page).limit(per_page).all()

            return {
                'items': items,
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page,
                'has_next': page < ((total + per_page - 1) // per_page),
                'has_prev': page > 1
            }
        except SQLAlchemyError as e:
            logger.error(f"사용자 대화 기록 조회 오류: {str(e)}")
            db.session.rollback()
            raise

    def get_recent_conversations(self, uid: int, limit: int = 5) -> List[Chatbot]:
        """
        최근 대화 목록 조회

        Args:
            uid (int): 사용자 ID
            limit (int): 최대 개수

        Returns:
            List[Chatbot]: 대화 목록
        """
        try:
            return Chatbot.query.filter_by(uid=uid) \
                .order_by(Chatbot.timestamp.desc()) \
                .limit(limit) \
                .all()
        except SQLAlchemyError as e:
            logger.error(f"최근 대화 목록 조회 오류: {str(e)}")
            db.session.rollback()
            raise

    def get_conversations_by_date(self, uid: int, start_date: datetime,
                                  end_date: datetime) -> List[Chatbot]:
        """
        날짜별 대화 목록 조회

        Args:
            uid (int): 사용자 ID
            start_date (datetime): 시작 날짜
            end_date (datetime): 종료 날짜

        Returns:
            List[Chatbot]: 대화 목록
        """
        try:
            return Chatbot.query.filter(
                Chatbot.uid == uid,
                Chatbot.timestamp >= start_date,
                Chatbot.timestamp <= end_date
            ).order_by(Chatbot.timestamp.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"날짜별 대화 목록 조회 오류: {str(e)}")
            db.session.rollback()
            raise

    def search_conversations(self, uid: int, keyword: str) -> List[Chatbot]:
        """
        대화 검색

        Args:
            uid (int): 사용자 ID
            keyword (str): 검색어

        Returns:
            List[Chatbot]: 대화 목록
        """
        try:
            return Chatbot.query.filter(
                Chatbot.uid == uid,
                (Chatbot.query.like(f'%{keyword}%')) | (Chatbot.response.like(f'%{keyword}%'))
            ).order_by(Chatbot.timestamp.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"대화 검색 오류: {str(e)}")
            db.session.rollback()
            raise

    def clear_conversation_history(self, uid: int) -> bool:
        """
        대화 기록 삭제

        Args:
            uid (int): 사용자 ID

        Returns:
            bool: 성공 여부
        """
        try:
            Chatbot.query.filter_by(uid=uid).delete()
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"대화 기록 삭제 오류: {str(e)}")
            db.session.rollback()
            raise

    def add_response(self, chatbot: Chatbot, response: str) -> Chatbot:
        """
        응답 추가

        Args:
            chatbot (Chatbot): 업데이트할 대화
            response (str): 추가할 응답

        Returns:
            Chatbot: 업데이트된 대화
        """
        return self.update(chatbot, response=response)