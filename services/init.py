from pathlib import Path
from typing import Dict, Any
import os
import logging
import json
from dotenv import load_dotenv

from services.food_database import FoodDatabaseService
from services.rag_service import RAGService
from services.data_processor import DataProcessorService

# 환경 변수 로드 및 확인
load_dotenv()
print(f"현재 작업 디렉토리: {os.getcwd()}")
print(f"OPENAI_API_KEY 존재 여부: {'있음' if os.getenv('OPENAI_API_KEY') else '없음'}")

# 디렉토리 생성
os.makedirs("logs", exist_ok=True)

# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/nutrition_service.log', mode='w')  # 'a' 대신 'w'로 변경
    ]
)

logger = logging.getLogger(__name__)
logger.info("서비스 모듈 초기화 시작")

def init_services() -> Dict[str, Any]:
    """
    서비스 초기화 함수

    Returns:
        Dict[str, Any]: 초기화된 서비스 객체들
    """
    try:
        logger.info("서비스 초기화 시작")
        print("서비스 초기화 시작")

        # 디렉토리 생성
        os.makedirs("database", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        os.makedirs("database/vector_db", exist_ok=True)  # RAG 디렉토리 명시적 생성
        print("디렉토리 생성 완료")

        # 환경 변수 확인
        openai_api_key = os.getenv("OPENAI_API_KEY")
        print(f"API 키 길이: {len(openai_api_key) if openai_api_key else 0}")
        if not openai_api_key:
            logger.warning("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
            print("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

        # 서비스 인스턴스 생성
        food_db_service = FoodDatabaseService(db_path="database/food_database.db")
        print("식품 데이터베이스 서비스 초기화 완료")

        data_processor = DataProcessorService(data_dir="database/data")
        print("데이터 처리 서비스 초기화 완료")

        # OpenAI API 키가 있는 경우에만 RAG 서비스 초기화
        rag_service = None
        if openai_api_key:
            try:
                print("RAG 서비스 초기화 시도...")
                rag_service = RAGService(
                    openai_api_key=openai_api_key,
                    vector_db_dir="database/vector_db"
                )
                print("RAG 서비스 초기화 성공")
                logger.info("RAG 서비스 초기화 성공")
            except Exception as e:
                print(f"RAG 서비스 초기화 오류: {str(e)}")
                logger.error(f"RAG 서비스 초기화 오류: {str(e)}")
        else:
            print("OpenAI API 키가 없어 RAG 서비스를 초기화하지 않습니다.")

        services = {
            "food_database": food_db_service,
            "data_processor": data_processor,
            "rag_service": rag_service
        }

        logger.info("서비스 초기화 완료")
        print(f"서비스 초기화 완료: {', '.join(f'{k}={v is not None}' for k, v in services.items())}")
        return services

    except Exception as e:
        logger.error(f"서비스 초기화 오류: {str(e)}")
        print(f"서비스 초기화 오류: {str(e)}")
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
        print("기본 데이터 임포트 시작")

        food_db = services.get("food_database")
        data_processor = services.get("data_processor")
        rag_service = services.get("rag_service")

        if not food_db or not data_processor:
            logger.error("서비스가 초기화되지 않았습니다.")
            print("서비스가 초기화되지 않았습니다.")
            return False

        # 기본 데이터 파일 경로
        default_food_csv = "database/default_data/korean_foods.csv"
        default_recipe_json = "database/default_data/korean_recipes.json"

        # 기본 데이터 디렉토리 생성
        os.makedirs("database/default_data", exist_ok=True)
        print(f"기본 데이터 디렉토리 생성 완료")

        # 기본 데이터 파일이 있는지 확인
        print(f"기본 식품 CSV 파일 존재 여부: {os.path.exists(default_food_csv)}")
        if os.path.exists(default_food_csv):
            # CSV 파일 처리
            processed_csv = data_processor.process_food_csv(default_food_csv)
            print(f"CSV 파일 처리 완료: {processed_csv}")

            # 식품 데이터베이스에 임포트
            food_count = food_db.import_food_data_from_csv(processed_csv)
            print(f"{food_count}개의 식품 데이터 임포트 완료")
            logger.info(f"{food_count}개의 식품 데이터 임포트 완료")

            # RAG 서비스가 있는 경우 문서 추가
            if rag_service:
                print("RAG 서비스에 문서 추가 시도...")
                # 모든 식품 가져오기
                conn = None
                try:
                    import sqlite3
                    conn = sqlite3.connect("database/food_database.db")
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()

                    cursor.execute("SELECT * FROM foods")
                    foods = [dict(row) for row in cursor.fetchall()]
                    print(f"{len(foods)}개의 식품 데이터 로드 완료")

                    doc_count = 0
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
                        if rag_service.add_documents([rag_doc]) > 0:
                            doc_count += 1

                    print(f"{doc_count}개의 RAG 문서 추가 완료")
                    logger.info(f"{doc_count}개의 RAG 문서 추가 완료")

                except Exception as e:
                    logger.error(f"RAG 문서 추가 오류: {str(e)}")
                    print(f"RAG 문서 추가 오류: {str(e)}")
                finally:
                    if conn:
                        conn.close()
            else:
                print("RAG 서비스가 없어 문서를 추가하지 않습니다.")
        else:
            print(f"기본 식품 CSV 파일이 없습니다: {default_food_csv}")

        logger.info("기본 데이터 임포트 완료")
        print("기본 데이터 임포트 완료")
        return True

    except Exception as e:
        logger.error(f"기본 데이터 임포트 오류: {str(e)}")
        print(f"기본 데이터 임포트 오류: {str(e)}")
        return False

# 내보낼 함수들
__all__ = ["init_services", "import_default_data"]