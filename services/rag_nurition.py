import logging
from typing import List, Dict, Any, Optional
import os
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import WebBaseLoader, TextLoader
from langchain.chains import RetrievalQA

class RAGNutritionService:
    """
    RAG(검색 증강 생성)를 활용한 영양 정보 서비스
    """
    def __init__(self, openai_api_key: str, data_sources_dir: str = 'nutrition_sources'):
        """
        RAG 영양 서비스 초기화

        Args:
            openai_api_key (str): OpenAI API 키
            data_sources_dir (str): 영양 관련 데이터 소스 디렉토리
        """
        self.logger = logging.getLogger(__name__)
        self.openai_api_key = openai_api_key
        self.data_sources_dir = data_sources_dir

        # 임베딩 및 언어 모델 초기화
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.llm = ChatOpenAI(
            openai_api_key=openai_api_key,
            model_name="gpt-3.5-turbo",
            temperature=0.3
        )

        # 벡터 저장소 초기화
        self.vectorstore = self._load_nutrition_sources()

    def _load_nutrition_sources(self) -> Any:
        """
        다양한 영양 관련 소스 로드 및 벡터화

        Returns:
            Chroma: 벡터화된 영양 데이터 저장소
        """
        try:
            # 문서 분할기 설정
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )

            # 문서 수집
            all_documents = []

            # 웹 소스 로드
            web_sources = [
                "https://www.health.harvard.edu/nutrition",
                "https://www.hsph.harvard.edu/nutritionsource/",
                "https://www.nal.usda.gov/legacy/food-and-nutrition-information-center"
            ]

            for source in web_sources:
                try:
                    loader = WebBaseLoader(source)
                    web_docs = loader.load()
                    web_splits = text_splitter.split_documents(web_docs)
                    all_documents.extend(web_splits)
                except Exception as e:
                    self.logger.warning(f"웹 소스 로드 실패: {source} - {str(e)}")

            # 로컬 텍스트 파일 로드 (존재할 경우)
            if os.path.exists(self.data_sources_dir):
                for filename in os.listdir(self.data_sources_dir):
                    if filename.endswith(('.txt', '.md')):
                        file_path = os.path.join(self.data_sources_dir, filename)
                        try:
                            loader = TextLoader(file_path)
                            local_docs = loader.load()
                            local_splits = text_splitter.split_documents(local_docs)
                            all_documents.extend(local_splits)
                        except Exception as e:
                            self.logger.warning(f"로컬 파일 로드 실패: {filename} - {str(e)}")

            # 벡터 저장소 생성
            return Chroma.from_documents(
                documents=all_documents,
                embedding=self.embeddings
            )

        except Exception as e:
            self.logger.error(f"영양 소스 로드 중 오류 발생: {str(e)}")
            return None

    def get_nutrition_insights(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """
        RAG를 활용한 영양 인사이트 제공

        Args:
            query (str): 사용자 질의
            top_k (int): 검색할 상위 문서 수

        Returns:
            Dict[str, Any]: 최신 영양학 연구 기반 인사이트
        """
        try:
            # 벡터 저장소 검색기 설정
            retriever = self.vectorstore.as_retriever(
                search_kwargs={"k": top_k}  # 상위 3개 문서 검색
            )

            # RetrievalQA 체인 생성
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True
            )

            # 질의 실행
            result = qa_chain({"query": query})

            return {
                "answer": result['result'],
                "sources": [
                    {
                        "content": doc.page_content,
                        "source": doc.metadata.get('source', 'Unknown')
                    }
                    for doc in result.get('source_documents', [])
                ]
            }

        except Exception as e:
            self.logger.error(f"영양 인사이트 생성 중 오류: {str(e)}")
            return {
                "answer": "현재 인사이트를 제공할 수 없습니다.",
                "sources": []
            }

    def update_nutrition_sources(self, new_sources: List[str]) -> bool:
        """
        새로운 영양 정보 소스 추가

        Args:
            new_sources (List[str]): 새로운 소스 URL 또는 파일 경로 목록

        Returns:
            bool: 소스 업데이트 성공 여부
        """
        try:
            # 새로운 소스 로드 및 벡터 저장소에 추가
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )

            new_documents = []

            for source in new_sources:
                try:
                    # URL인 경우
                    if source.startswith(('http://', 'https://')):
                        loader = WebBaseLoader(source)
                        docs = loader.load()
                    # 로컬 파일인 경우
                    else:
                        loader = TextLoader(source)
                        docs = loader.load()

                    splits = text_splitter.split_documents(docs)
                    new_documents.extend(splits)
                except Exception as e:
                    self.logger.warning(f"소스 로드 실패: {source} - {str(e)}")

            # 기존 벡터 저장소에 새 문서 추가
            if new_documents:
                self.vectorstore.add_documents(new_documents)
                self.logger.info(f"{len(new_documents)}개의 새로운 문서 추가됨")
                return True

            return False

        except Exception as e:
            self.logger.error(f"소스 업데이트 중 오류 발생: {str(e)}")
            return False