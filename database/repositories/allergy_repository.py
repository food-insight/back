from database.repositories.base_repository import BaseRepository
from models.allergy import Allergy
from app.extensions import db
from typing import Optional, List, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

class AllergyRepository(BaseRepository[Allergy]):
    """알레르기 저장소 클래스"""

    def __init__(self):
        """알레르기 저장소 초기화"""
        super().__init__(Allergy)

    def create_allergy(self, uid: int, allergy_name: str, fid: Optional[int] = None) -> Allergy:
        """
        알레르기 정보 생성

        Args:
            uid (int): 사용자 ID
            allergy_name (str): 알레르기 이름
            fid (Optional[int]): 음식 ID

        Returns:
            Allergy: 생성된 알레르기 정보
        """
        return self.create(
            uid=uid,
            allergy_name=allergy_name,
            fid=fid
        )

    def get_user_allergies(self, uid: int) -> List[Allergy]:
        """
        사용자 알레르기 목록 조회

        Args:
            uid (int): 사용자 ID

        Returns:
            List[Allergy]: 알레르기 목록
        """
        return self.find_by(uid=uid)

    def check_existing_allergy(self, uid: int, allergy_name: str) -> bool:
        """
        사용자의 특정 알레르기 존재 여부 확인

        Args:
            uid (int): 사용자 ID
            allergy_name (str): 알레르기 이름

        Returns:
            bool: 존재 여부
        """
        return self.exists(uid=uid, allergy_name=allergy_name)

    def delete_allergy(self, allergy_id: int, uid: int) -> bool:
        """
        알레르기 정보 삭제 (사용자 ID 검증)

        Args:
            allergy_id (int): 알레르기 ID
            uid (int): 사용자 ID

        Returns:
            bool: 성공 여부
        """
        try:
            allergy = Allergy.query.filter_by(aid=allergy_id, uid=uid).first()
            if not allergy:
                return False

            db.session.delete(allergy)
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"알레르기 삭제 오류: {str(e)}")
            db.session.rollback()
            raise

    def delete_all_user_allergies(self, uid: int) -> bool:
        """
        사용자의 모든 알레르기 정보 삭제

        Args:
            uid (int): 사용자 ID

        Returns:
            bool: 성공 여부
        """
        try:
            Allergy.query.filter_by(uid=uid).delete()
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"모든 알레르기 삭제 오류: {str(e)}")
            db.session.rollback()
            raise

    def batch_create_allergies(self, uid: int, allergy_names: List[str]) -> List[Allergy]:
        """
        여러 알레르기 정보 일괄 생성

        Args:
            uid (int): 사용자 ID
            allergy_names (List[str]): 알레르기 이름 목록

        Returns:
            List[Allergy]: 생성된 알레르기 목록
        """
        try:
            allergies = []

            for allergy_name in allergy_names:
                # 중복 확인
                existing = self.find_one_by(uid=uid, allergy_name=allergy_name)
                if not existing:
                    allergy = Allergy(uid=uid, allergy_name=allergy_name)
                    allergies.append(allergy)

            db.session.add_all(allergies)
            db.session.commit()

            return allergies
        except SQLAlchemyError as e:
            logger.error(f"알레르기 일괄 생성 오류: {str(e)}")
            db.session.rollback()
            raise