from database.repositories.base_repository import BaseRepository
from models.recommendation import Recommendation
from app.extensions import db
from typing import Optional, List, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

class RecommendationRepository(BaseRepository[Recommendation]):
    """추천 저장소 클래스"""

    def __init__(self):
        """추천 저장소 초기화"""
        super().__init__(Recommendation)

    def create_recommendation(self, uid: int, reason: Optional[str] = None,
                              content: Optional[Dict] = None, mid: Optional[int] = None,
                              fid: Optional[int] = None) -> Recommendation:
        """
        추천 생성

        Args:
            uid (int): 사용자 ID
            reason (Optional[str]): 추천 이유
            content (Optional[Dict]): 추천 내용
            mid (Optional[int]): 식사 ID
            fid (Optional[int]): 음식 ID

        Returns:
            Recommendation: 생성된 추천
        """
        content_str = None
        if content:
            content_str = json.dumps(content)

        return self.create(
            uid=uid,
            reason=reason,
            content=content_str,
            mid=mid,
            fid=fid
        )

    def get_user_recommendations(self, uid: int, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        사용자 추천 목록 페이지네이션

        Args:
            uid (int): 사용자 ID
            page (int): 페이지 번호
            per_page (int): 페이지당 항목 수

        Returns:
            Dict[str, Any]: 페이지네이션 결과
        """
        return self.paginate(page=page, per_page=per_page, uid=uid)

    def get_recent_recommendations(self, uid: int, limit: int = 5) -> List[Recommendation]:
        """
        최근 추천 목록 조회

        Args:
            uid (int): 사용자 ID
            limit (int): 최대 개수

        Returns:
            List[Recommendation]: 추천 목록
        """
        try:
            return Recommendation.query.filter_by(uid=uid) \
                .order_by(Recommendation.created_at.desc()) \
                .limit(limit) \
                .all()
        except SQLAlchemyError as e:
            logger.error(f"최근 추천 목록 조회 오류: {str(e)}")
            db.session.rollback()
            raise

    def get_meal_recommendations(self, uid: int, mid: int) -> List[Recommendation]:
        """
        특정 식사에 대한 추천 목록 조회

        Args:
            uid (int): 사용자 ID
            mid (int): 식사 ID

        Returns:
            List[Recommendation]: 추천 목록
        """
        return self.find_by(uid=uid, mid=mid)

    def get_food_recommendations(self, uid: int, fid: int) -> List[Recommendation]:
        """
        특정 음식에 대한 추천 목록 조회

        Args:
            uid (int): 사용자 ID
            fid (int): 음식 ID

        Returns:
            List[Recommendation]: 추천 목록
        """
        return self.find_by(uid=uid, fid=fid)

    def get_recommendations_by_date(self, uid: int, start_date: datetime,
                                    end_date: datetime) -> List[Recommendation]:
        """
        날짜별 추천 목록 조회

        Args:
            uid (int): 사용자 ID
            start_date (datetime): 시작 날짜
            end_date (datetime): 종료 날짜

        Returns:
            List[Recommendation]: 추천 목록
        """
        try:
            return Recommendation.query.filter(
                Recommendation.uid == uid,
                Recommendation.created_at >= start_date,
                Recommendation.created_at <= end_date
            ).order_by(Recommendation.created_at.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"날짜별 추천 목록 조회 오류: {str(e)}")
            db.session.rollback()
            raise

    def search_recommendations(self, uid: int, keyword: str) -> List[Recommendation]:
        """
        추천 검색

        Args:
            uid (int): 사용자 ID
            keyword (str): 검색어

        Returns:
            List[Recommendation]: 추천 목록
        """
        try:
            return Recommendation.query.filter(
                Recommendation.uid == uid,
                Recommendation.reason.like(f'%{keyword}%')
            ).order_by(Recommendation.created_at.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"추천 검색 오류: {str(e)}")
            db.session.rollback()
            raise

    def update_recommendation_content(self, recommendation: Recommendation, content: Dict) -> Recommendation:
        """
        추천 내용 업데이트

        Args:
            recommendation (Recommendation): 업데이트할 추천
            content (Dict): 업데이트할 내용

        Returns:
            Recommendation: 업데이트된 추천
        """
        try:
            content_str = json.dumps(content)
            return self.update(recommendation, content=content_str)
        except SQLAlchemyError as e:
            logger.error(f"추천 내용 업데이트 오류: {str(e)}")
            db.session.rollback()
            raise