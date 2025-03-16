import os
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from langchain_community.embeddings import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA

class RAGService:
    """RAG(Retrieval-Augmented Generation) 서비스"""

    def __init__(
            self,
            openai_api_key: str,
            vector_db_dir: str = "database/vector_db",
            model_name: str = "gpt-3.5-turbo",
            chunk_size: int = 1000,
            chunk_overlap: int = 200
    ):
        """
        RAG 서비스 초기화

        Args:
            openai_api_key (str): OpenAI API 키
            vector_db_dir (str): 벡터 데이터베이스 디렉토리
            model_name (str): 사용할 모델 이름
            chunk_size (int): 청크 크기
            chunk_overlap (int): 청크 겹침 크기
        """
        self.logger = logging.getLogger(__name__)
        self.vector_db_dir = vector_db_dir
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # 디렉토리 생성
        os.makedirs(vector_db_dir, exist_ok=True)

        # OpenAI 설정
        self.openai_api_key = openai_api_key
        self.model_name = model_name

        # 임베딩 및 벡터 저장소 초기화
        self._init_embedding_model()
        self._load_or_create_vector_db()

    def _init_embedding_model(self):
        """임베딩 모델 초기화"""
        try:
            self.embeddings = OpenAIEmbeddings(openai_api_key=self.openai_api_key)
            self.logger.info("임베딩 모델 초기화 완료")
        except Exception as e:
            self.logger.error(f"임베딩 모델 초기화 오류: {str(e)}")
            raise

    def _load_or_create_vector_db(self):
        """벡터 데이터베이스 로드 또는 생성"""
        try:
            # 기존 벡터 DB 로드 시도
            if os.path.exists(os.path.join(self.vector_db_dir, "chroma.sqlite3")):
                self.logger.info("기존 벡터 데이터베이스 로드")
                self.vector_db = Chroma(
                    persist_directory=self.vector_db_dir,
                    embedding_function=self.embeddings
                )
            else:
                self.logger.info("벡터 데이터베이스가 없습니다. 비어있는 데이터베이스 생성")
                # 빈 문서 리스트로 초기화
                self.vector_db = Chroma(
                    persist_directory=self.vector_db_dir,
                    embedding_function=self.embeddings
                )
                self.vector_db.persist()
        except Exception as e:
            self.logger.error(f"벡터 데이터베이스 로드 오류: {str(e)}")
            raise

    def add_documents(self, documents: List[Dict[str, Any]]) -> int:
        """
        문서 추가

        Args:
            documents (List[Dict[str, Any]]): 추가할 문서 목록

        Returns:
            int: 추가된 문서 수
        """
        try:
            langchain_docs = []

            for doc in documents:
                content = doc.get("content", "")
                metadata = doc.get("metadata", {})

                langchain_docs.append(Document(
                    page_content=content,
                    metadata=metadata
                ))

            # 문서 분할
            text_splitter = CharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
            split_docs = text_splitter.split_documents(langchain_docs)

            # 벡터 데이터베이스에 추가
            self.vector_db.add_documents(split_docs)
            self.vector_db.persist()

            self.logger.info(f"문서 추가 완료: {len(split_docs)}개 청크 생성")
            return len(split_docs)

        except Exception as e:
            self.logger.error(f"문서 추가 오류: {str(e)}")
            return 0

    def add_nutrition_document(self, nutrition_data: Dict[str, Any]) -> bool:
        """
        영양 정보 문서 추가

        Args:
            nutrition_data (Dict[str, Any]): 영양 정보 데이터

        Returns:
            bool: 성공 여부
        """
        try:
            self.logger.info(f"영양 정보 문서 추가: {nutrition_data.get('name', 'Untitled')}")

            # 문서 내용 생성
            content = f"""
식품명: {nutrition_data.get('name', 'Untitled')}
카테고리: {nutrition_data.get('category', '기타')}
영양정보:
- 칼로리: {nutrition_data.get('calories', 0)}kcal
- 탄수화물: {nutrition_data.get('carbs', 0)}g
- 단백질: {nutrition_data.get('protein', 0)}g
- 지방: {nutrition_data.get('fat', 0)}g
- 나트륨: {nutrition_data.get('sodium', 0)}mg
- 식이섬유: {nutrition_data.get('fiber', 0)}g
- 당류: {nutrition_data.get('sugar', 0)}g
태그: {', '.join(nutrition_data.get('tags', []))}
설명: {nutrition_data.get('description', '')}
"""

            # 문서 객체 생성
            doc = {
                "content": content,
                "metadata": {
                    "type": "nutrition",
                    "name": nutrition_data.get('name', 'Untitled'),
                    "category": nutrition_data.get('category', '기타'),
                    "added_at": datetime.now().isoformat()
                }
            }

            # 문서 추가
            result = self.add_documents([doc])

            return result > 0

        except Exception as e:
            self.logger.error(f"영양 정보 문서 추가 오류: {str(e)}")
            return False

    def get_nutrition_insights(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """
        영양 인사이트 생성

        Args:
            query (str): 질의 문자열
            top_k (int): 검색할 상위 문서 수

        Returns:
            Dict[str, Any]: 생성된 인사이트
        """
        try:
            self.logger.info(f"영양 인사이트 생성 시작: {query}")

            # RAG 체인 생성
            llm = ChatOpenAI(
                openai_api_key=self.openai_api_key,
                model_name=self.model_name,
                temperature=0.3
            )

            retriever = self.vector_db.as_retriever(search_kwargs={"k": top_k})

            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True
            )

            # 질의 실행
            result = qa_chain({"query": query})

            # 소스 문서 추출
            source_documents = []
            for doc in result.get("source_documents", []):
                source_documents.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata
                })

            return {
                "answer": result["result"],
                "source_documents": source_documents,
                "query": query,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"영양 인사이트 생성 오류: {str(e)}")
            return {
                "answer": "인사이트를 생성할 수 없습니다.",
                "error": str(e),
                "query": query,
                "timestamp": datetime.now().isoformat()
            }