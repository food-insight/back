import os
import sys
import logging
import argparse
import time
from dotenv import load_dotenv

# 프로젝트 루트 디렉토리를 가져와 sys.path에 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from services.init import init_services
from utils.data_pipeline_tasks import (
    create_sample_food_data_csv,
    create_sample_recipes_json,
    create_sample_nutrition_articles,
    process_and_import_food_csv,
    import_nutrition_articles,
    synchronize_food_database_to_rag
)

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/data_pipeline.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)

def init_data_pipeline(sample_data: bool = True, sync_rag: bool = True):
    """
    데이터 파이프라인 초기화

    Args:
        sample_data (bool): 샘플 데이터 생성 여부
        sync_rag (bool): RAG 동기화 여부
    """
    try:
        start_time = time.time()
        logger.info("데이터 파이프라인 초기화 시작")

        # 디렉토리 생성
        os.makedirs("database", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        os.makedirs("database/data", exist_ok=True)
        os.makedirs("database/default_data", exist_ok=True)

        # 서비스 초기화
        services = init_services()

        # 필요한 서비스 확인
        if not services.get("food_database"):
            logger.error("식품 데이터베이스 서비스가 초기화되지 않았습니다.")
            return False

        # 샘플 데이터 생성
        if sample_data:
            logger.info("샘플 데이터 생성 시작")
            food_csv_path = create_sample_food_data_csv()
            recipe_json_path = create_sample_recipes_json()
            article_count = create_sample_nutrition_articles()
            logger.info(f"샘플 데이터 생성 완료: 식품 CSV({food_csv_path}), 레시피 JSON({recipe_json_path}), 문서({article_count}개)")

            # 샘플 데이터 임포트
            if food_csv_path:
                food_count = process_and_import_food_csv(food_csv_path, services)
                logger.info(f"샘플 식품 데이터 임포트 완료: {food_count}개")

            # 영양 문서 임포트 (RAG 서비스가 있는 경우)
            if services.get("rag_service"):
                doc_count = import_nutrition_articles("database/data/nutrition_articles", services)
                logger.info(f"샘플 영양 문서 임포트 완료: {doc_count}개")

        # 데이터베이스와 RAG 동기화
        if sync_rag and services.get("rag_service"):
            logger.info("데이터베이스와 RAG 동기화 시작")
            sync_count = synchronize_food_database_to_rag(services)
            logger.info(f"데이터베이스와 RAG 동기화 완료: {sync_count}개 문서")

        elapsed_time = time.time() - start_time
        logger.info(f"데이터 파이프라인 초기화 완료. 소요 시간: {elapsed_time:.2f}초")
        return True

    except Exception as e:
        logger.error(f"데이터 파이프라인 초기화 오류: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='데이터 파이프라인 초기화 스크립트')
    parser.add_argument('--no-sample', action='store_true', help='샘플 데이터 생성 건너뛰기')
    parser.add_argument('--no-sync', action='store_true', help='RAG 동기화 건너뛰기')
    parser.add_argument('--import-csv', type=str, help='추가로 임포트할 CSV 파일 경로')
    parser.add_argument('--import-articles', type=str, help='추가로 임포트할 문서 디렉토리 경로')

    args = parser.parse_args()

    # 데이터 파이프라인 초기화
    result = init_data_pipeline(
        sample_data=not args.no_sample,
        sync_rag=not args.no_sync
    )

    # 추가 데이터 임포트
    if result and args.import_csv:
        services = init_services()
        count = process_and_import_food_csv(args.import_csv, services)
        logger.info(f"추가 CSV 파일 임포트 완료: {count}개")

    if result and args.import_articles:
        services = init_services()
        count = import_nutrition_articles(args.import_articles, services)
        logger.info(f"추가 문서 임포트 완료: {count}개")

    return 0 if result else 1

if __name__ == "__main__":
    exit(main())