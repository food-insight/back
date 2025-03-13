from database.repositories.base_repository import BaseRepository
from models.ragdata import RagData
from app.extensions import db
from typing import Optional, List, Dict, Any, Union
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_, and_
from datetime import datetime
import logging
import json
import numpy as np

logger = logging.getLogger(__name__)

class RagDataRepository(BaseRepository[RagData]):
    """RAG 데이터 저장소 클래스"""

    def __init__(self):
        """RAG 데이터 저장소 초기화"""
        super().__init__(RagData)

    def create_ragdata(self, source: str, content: str, metadata: Optional[Dict] = None,
                       embedding: Optional[List[float]] = None) -> RagData:
        """
        RAG 데이터 생성

        Args:
            source (str): 데이터 출처
            content (str): 실제 콘텐츠
            metadata (Optional[Dict]): 메타데이터
            embedding (Optional[List[float]]): 벡터 임베딩

        Returns:
            RagData: 생성된 RAG 데이터
        """
        return self.create(
            source=source,
            content=content,
            metadata=metadata,
            embedding=embedding
        )

    def search_by_content(self, query: str, limit: int = 10) -> List[RagData]:
        """
        콘텐츠 검색

        Args:
            query (str): 검색어
            limit (int): 최대 개수

        Returns:
            List[RagData]: RAG 데이터 목록
        """
        try:
            return RagData.query.filter(
                RagData.content.like(f'%{query}%')
            ).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"콘텐츠 검색 오류: {str(e)}")
            db.session.rollback()
            raise

    def search_by_source(self, source: str) -> List[RagData]:
        """
        출처로 검색

        Args:
            source (str): 출처

        Returns:
            List[RagData]: RAG 데이터 목록
        """
        return self.find_by(source=source)

    def search_by_metadata(self, metadata_key: str, metadata_value: Any) -> List[RagData]:
        """
        메타데이터로 검색

        Args:
            metadata_key (str): 메타데이터 키
            metadata_value (Any): 메타데이터 값

        Returns:
            List[RagData]: RAG 데이터 목록
        """
        try:
            # JSON에서 특정 키의 값으로 검색
            search_pattern = f'%"{metadata_key}": "{metadata_value}"%'
            if isinstance(metadata_value, (int, float)):
                search_pattern = f'%"{metadata_key}": {metadata_value}%'

            return RagData.query.filter(
                RagData.metadata.like(search_pattern)
            ).all()
        except SQLAlchemyError as e:
            logger.error(f"메타데이터 검색 오류: {str(e)}")
            db.session.rollback()
            raise

    def vector_search(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        벡터 검색 (유사도 기반)

        Args:
            query_vector (List[float]): 쿼리 벡터
            top_k (int): 상위 K개 결과

        Returns:
            List[Dict[str, Any]]: 검색 결과 목록
        """
        try:
            # 모든 데이터 가져오기
            all_data = RagData.query.filter(RagData.embedding.isnot(None)).all()

            # 벡터 유사도 계산
            results = []
            query_vector_np = np.array(query_vector)

            for data in all_data:
                try:
                    embedding = data.get_embedding()
                    if embedding:
                        embedding_np = np.array(embedding)

                        # 코사인 유사도 계산
                        similarity = np.dot(query_vector_np, embedding_np) / (
                                np.linalg.norm(query_vector_np) * np.linalg.norm(embedding_np))

                        results.append({
                            'data': data,
                            'similarity': float(similarity)
                        })
                except Exception as e:
                    logger.error(f"벡터 유사도 계산 오류: {str(e)}")
                    continue

            # 유사도 기준 정렬 후 상위 K개 반환
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:top_k]
        except Exception as e:
            logger.error(f"벡터 검색 오류: {str(e)}")
            return []

    def update_embedding(self, ragdata: RagData, embedding: List[float]) -> RagData:
        """
        벡터 임베딩 업데이트

        Args:
            ragdata (RagData): 업데이트할 RAG 데이터
            embedding (List[float]): 벡터 임베딩

        Returns:
            RagData: 업데이트된 RAG 데이터
        """
        try:
            embedding_str = json.dumps(embedding)
            return self.update(ragdata, embedding=embedding_str)
        except SQLAlchemyError as e:
            logger.error(f"벡터 임베딩 업데이트 오류: {str(e)}")
            db.session.rollback()
            raise

    def batch_insert(self, data_list: List[Dict[str, Any]]) -> List[RagData]:
        """
        배치 삽입

        Args:
            data_list (List[Dict[str, Any]]): 삽입할 데이터 목록

        Returns:
            List[RagData]: 생성된 RAG 데이터 목록
        """
        try:
            ragdata_list = []

            for data in data_list:
                metadata = data.get('metadata')
                embedding = data.get('embedding')

                # JSON 변환
                metadata_str = json.dumps(metadata) if metadata else None
                embedding_str = json.dumps(embedding) if embedding else None

                ragdata = RagData(
                    source=data['source'],
                    content=data['content'],
                    metadata=metadata_str,
                    embedding=embedding_str
                )

                ragdata_list.append(ragdata)

            db.session.add_all(ragdata_list)
            db.session.commit()

            return ragdata_list
        except SQLAlchemyError as e:
            logger.error(f"배치 삽입 오류: {str(e)}")
            db.session.rollback()
            raise

    def get_data_by_date_range(self, start_date: datetime, end_date: datetime) -> List[RagData]:
        """
        날짜 범위로 데이터 조회

        Args:
            start_date (datetime): 시작 날짜
            end_date (datetime): 종료 날짜

        Returns:
            List[RagData]: RAG 데이터 목록
        """
        try:
            return RagData.query.filter(
                RagData.created_at >= start_date,
                RagData.created_at <= end_date
            ).order_by(RagData.created_at.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"날짜 범위 데이터 조회 오류: {str(e)}")
            db.session.rollback()
            raise