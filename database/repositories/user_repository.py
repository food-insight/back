from database.repositories.base_repository import BaseRepository
from models.user import User
from app.extensions import db
from typing import Optional, List, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

class UserRepository(BaseRepository[User]):
    """사용자 저장소 클래스"""

    def __init__(self):
        """사용자 저장소 초기화"""
        super().__init__(User)

    def find_by_email(self, email: str) -> Optional[User]:
        """
        이메일로 사용자 찾기

        Args:
            email (str): 사용자 이메일

        Returns:
            Optional[User]: 찾은 사용자 또는 None
        """
        return self.find_one_by(email=email)

    def create_user(self, email: str, password: str, name: str, gender: Optional[int] = None,
                    birth: Optional[str] = None, allergies: Optional[str] = None,
                    health_goal: Optional[str] = None) -> User:
        """
        새 사용자 생성

        Args:
            email (str): 이메일
            password (str): 비밀번호
            name (str): 이름
            gender (Optional[int]): 성별 (0: 남성, 1: 여성)
            birth (Optional[str]): 생년월일
            allergies (Optional[str]): 알레르기 정보
            health_goal (Optional[str]): 건강 목표

        Returns:
            User: 생성된 사용자
        """
        return self.create(
            email=email,
            password=password,
            name=name,
            gender=gender,
            birth=birth,
            allergies=allergies,
            health_goal=health_goal
        )

    def update_profile(self, user: User, **kwargs) -> User:
        """
        사용자 프로필 업데이트

        Args:
            user (User): 업데이트할 사용자
            **kwargs: 업데이트할 속성

        Returns:
            User: 업데이트된 사용자
        """
        # 비밀번호 업데이트는 별도 처리
        if 'password' in kwargs:
            user.update_password(kwargs.pop('password'))

        return self.update(user, **kwargs)

    def get_users_with_health_goal(self) -> List[User]:
        """
        건강 목표가 있는 사용자 목록 조회

        Returns:
            List[User]: 사용자 목록
        """
        try:
            return User.query.filter(User.health_goal.isnot(None)).all()
        except SQLAlchemyError as e:
            logger.error(f"건강 목표 사용자 조회 오류: {str(e)}")
            db.session.rollback()
            raise

    def get_users_with_allergies(self) -> List[User]:
        """
        알레르기 정보가 있는 사용자 목록 조회

        Returns:
            List[User]: 사용자 목록
        """
        try:
            return User.query.filter(User.allergies.isnot(None)).all()
        except SQLAlchemyError as e:
            logger.error(f"알레르기 사용자 조회 오류: {str(e)}")
            db.session.rollback()
            raise

    def search_users(self, keyword: str, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        사용자 검색

        Args:
            keyword (str): 검색어
            page (int): 페이지 번호
            per_page (int): 페이지당 항목 수

        Returns:
            Dict[str, Any]: 페이지네이션 결과
        """
        try:
            query = User.query.filter(
                (User.name.like(f'%{keyword}%')) |
                (User.email.like(f'%{keyword}%'))
            )

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
            logger.error(f"사용자 검색 오류: {str(e)}")
            db.session.rollback()
            raise