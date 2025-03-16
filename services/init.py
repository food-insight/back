from pathlib import Path
from typing import Dict, Any
import os
import logging
import json
from dotenv import load_dotenv

from services.food_database import FoodDatabaseService
from services.rag_service import RAGService
from services.data_processor import DataProcessorService

# 환경 변수 로드
load_dotenv()

# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/nutrition_service.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)

def init_services() -> Dict[str, Any]:
    """
    서비스 초기화 함수

    Returns:
        Dict[str, Any]: 초기화된 서비스 객체들
    """
    try:
        logger.info("서비스 초기화 시작")

        # 디렉토리 생성
        os.makedirs("database", exist_ok=True)
        os.makedirs("logs", exist_ok=True)

        # 환경 변수 확인
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            logger.warning("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

        # 서비스 인스턴스 생성
        food_db_service = FoodDatabaseService(db_path="database/food_database.db")
        data_processor = DataProcessorService(data_dir="database/data")

        # OpenAI API 키가 있는 경우에만 RAG 서비스 초기화
        rag_service = None
        if openai_api_key:
            rag_service = RAGService(
                openai_api_key=openai_api_key,
                vector_db_dir="database/vector_db"
            )

        services = {
            "food_database": food_db_service,
            "data_processor": data_processor,
            "rag_service": rag_service
        }

        logger.info("서비스 초기화 완료")
        return services

    except Exception as e:
        logger.error(f"서비스 초기화 오류: {str(e)}")
        # 최소한의 서비스라도 반환
        return {
            "food_database": None,
            "data_processor": None,
            "rag_service": None
        }

def import_default_data(services: Dict[str, Any]) -> bool:
    """
    기본 데이터 임포트 함수

    Args:
        services (Dict[str, Any]): 서비스 객체들

    Returns:
        bool: 성공 여부
    """
    try:
        logger.info("기본 데이터 임포트 시작")

        food_db = services.get("food_database")
        data_processor = services.get("data_processor")
        rag_service = services.get("rag_service")

        if not food_db or not data_processor:
            logger.error("서비스가 초기화되지 않았습니다.")
            return False

        # 기본 데이터 파일 경로
        default_food_csv = "database/default_data/korean_foods.csv"
        default_recipe_json = "database/default_data/korean_recipes.json"

        # 기본 데이터 디렉토리 생성
        os.makedirs("database/default_data", exist_ok=True)

        # 기본 데이터 파일이 있는지 확인
        if os.path.exists(default_food_csv):
            # CSV 파일 처리
            processed_csv = data_processor.process_food_csv(default_food_csv)

            # 식품 데이터베이스에 임포트
            food_count = food_db.import_food_data_from_csv(processed_csv)
            logger.info(f"{food_count}개의 식품 데이터 임포트 완료")

            # RAG 서비스가 있는 경우 문서 추가
            if rag_service:
                # 모든 식품 가져오기
                conn = None
                try:
                    import sqlite3
                    conn = sqlite3.connect("database/food_database.db")
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()

                    cursor.execute("SELECT * FROM foods")
                    foods = [dict(row) for row in cursor.fetchall()]

                    for food in foods:
                        # 태그 파싱
                        if "tags" in food and food["tags"]:
                            try:
                                food["tags"] = json.loads(food["tags"])
                            except:
                                food["tags"] = []
                        else:
                            food["tags"] = []

                        # RAG 문서로 변환 및 추가
                        rag_doc = data_processor.convert_food_data_to_rag_document(food)
                        rag_service.add_documents([rag_doc])

                except Exception as e:
                    logger.error(f"RAG 문서 추가 오류: {str(e)}")
                finally:
                    if conn:
                        conn.close()

        logger.info("기본 데이터 임포트 완료")
        return True

    except Exception as e:
        logger.error(f"기본 데이터 임포트 오류: {str(e)}")
        return False

# 내보낼 함수들
__all__ = ["init_services", "import_default_data"]