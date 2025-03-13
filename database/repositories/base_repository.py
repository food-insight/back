from app.extensions import db
from typing import TypeVar, Generic, Type, List, Optional, Any, Dict, Union
from sqlalchemy.exc import SQLAlchemyError
import logging

# 모델 타입 변수 정의
T = TypeVar('T')

logger = logging.getLogger(__name__)

class BaseRepository(Generic[T]):
    """기본 저장소 클래스"""

    def __init__(self, model_class: Type[T]):
        """
        저장소 초기화
        
        Args:
            model_class (Type[T]): 모델 클래스
        """
        self.model_class = model_class

    def get_by_id(self, id: Any) -> Optional[T]:
        """
        ID로 모델 찾기
        
        Args:
            id: 모델 ID
            
        Returns:
            Optional[T]: 찾은 모델 또는 None
        """
        try:
            return self.model_class.query.get(id)
        except SQLAlchemyError as e:
            logger.error(f"{self.model_class.__name__} ID {id} 조회 오류: {str(e)}")
            db.session.rollback()
            raise

    def get_all(self) -> List[T]:
        """
        모든 모델 가져오기
        
        Returns:
            List[T]: 모델 목록
        """
        try:
            return self.model_class.query.all()
        except SQLAlchemyError as e:
            logger.error(f"{self.model_class.__name__} 전체 조회 오류: {str(e)}")
            db.session.rollback()
            raise

    def find_by(self, **kwargs) -> List[T]:
        """
        조건으로 모델 찾기
        
        Args:
            **kwargs: 필터링 조건
            
        Returns:
            List[T]: 조건에 맞는 모델 목록
        """
        try:
            return self.model_class.query.filter_by(**kwargs).all()
        except SQLAlchemyError as e:
            logger.error(f"{self.model_class.__name__} 조건 조회 오류: {str(e)}")
            db.session.rollback()
            raise

    def find_one_by(self, **kwargs) -> Optional[T]:
        """
        조건으로 단일 모델 찾기
        
        Args:
            **kwargs: 필터링 조건
            
        Returns:
            Optional[T]: 찾은 모델 또는 None
        """
        try:
            return self.model_class.query.filter_by(**kwargs).first()
        except SQLAlchemyError as e:
            logger.error(f"{self.model_class.__name__} 단일 조건 조회 오류: {str(e)}")
            db.session.rollback()
            raise

    def create(self, **kwargs) -> T:
        """
        새 모델 생성
        
        Args:
            **kwargs: 모델 속성
            
        Returns:
            T: 생성된 모델
        """
        try:
            instance = self.model_class(**kwargs)
            db.session.add(instance)
            db.session.commit()
            return instance
        except SQLAlchemyError as e:
            logger.error(f"{self.model_class.__name__} 생성 오류: {str(e)}")
            db.session.rollback()
            raise

    def update(self, instance: T, **kwargs) -> T:
        """
        모델 업데이트
        
        Args:
            instance (T): 업데이트할 모델 인스턴스
            **kwargs: 업데이트할 속성
            
        Returns:
            T: 업데이트된 모델
        """
        try:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)

            db.session.commit()
            return instance
        except SQLAlchemyError as e:
            logger.error(f"{self.model_class.__name__} 업데이트 오류: {str(e)}")
            db.session.rollback()
            raise

    def delete(self, instance: T) -> bool:
        """
        모델 삭제
        
        Args:
            instance (T): 삭제할 모델 인스턴스
            
        Returns:
            bool: 성공 여부
        """
        try:
            db.session.delete(instance)
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"{self.model_class.__name__} 삭제 오류: {str(e)}")
            db.session.rollback()
            raise

    def delete_by_id(self, id: Any) -> bool:
        """
        ID로 모델 삭제
        
        Args:
            id: 삭제할 모델 ID
            
        Returns:
            bool: 성공 여부
        """
        instance = self.get_by_id(id)
        if instance:
            return self.delete(instance)
        return False

    def count(self, **kwargs) -> int:
        """
        조건에 맞는 모델 수 계산
        
        Args:
            **kwargs: 필터링 조건
            
        Returns:
            int: 모델 수
        """
        try:
            return self.model_class.query.filter_by(**kwargs).count()
        except SQLAlchemyError as e:
            logger.error(f"{self.model_class.__name__} 카운트 오류: {str(e)}")
            db.session.rollback()
            raise

    def exists(self, **kwargs) -> bool:
        """
        조건에 맞는 모델 존재 여부 확인
        
        Args:
            **kwargs: 필터링 조건
            
        Returns:
            bool: 존재 여부
        """
        return self.count(**kwargs) > 0

    def paginate(self, page: int = 1, per_page: int = 10, **kwargs) -> Dict[str, Any]:
        """
        페이지네이션
        
        Args:
            page (int): 페이지 번호
            per_page (int): 페이지당 항목 수
            **kwargs: 필터링 조건
            
        Returns:
            Dict[str, Any]: 페이지네이션 결과
        """
        try:
            query = self.model_class.query.filter_by(**kwargs)
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
            logger.error(f"{self.model_class.__name__} 페이지네이션 오류: {str(e)}")
            db.session.rollback()
            raise