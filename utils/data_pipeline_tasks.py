import os
import logging
import json
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import time

from services.food_database import FoodDatabaseService
from services.rag_service import RAGService
from services.data_processor import DataProcessorService

logger = logging.getLogger(__name__)

def process_and_import_food_csv(csv_path: str, services: Dict[str, Any]) -> int:
    """
    식품 CSV 파일 처리 및 임포트 태스크

    Args:
        csv_path (str): CSV 파일 경로
        services (Dict[str, Any]): 서비스 객체들

    Returns:
        int: 임포트된 식품 수
    """
    try:
        logger.info(f"식품 CSV 파일 처리 및 임포트 시작: {csv_path}")

        food_db = services.get("food_database")
        data_processor = services.get("data_processor")
        rag_service = services.get("rag_service")

        if not food_db or not data_processor:
            logger.error("필요한 서비스가 초기화되지 않았습니다.")
            return 0

        # 1. CSV 파일 전처리
        start_time = time.time()
        processed_csv = data_processor.process_food_csv(csv_path)
        preprocess_time = time.time() - start_time
        logger.info(f"전처리 완료. 소요 시간: {preprocess_time:.2f}초")

        # 2. 식품 데이터베이스에 임포트
        start_time = time.time()
        food_count = food_db.import_food_data_from_csv(processed_csv)
        import_time = time.time() - start_time
        logger.info(f"데이터베이스 임포트 완료. 소요 시간: {import_time:.2f}초")

        # 3. RAG 서비스가 있는 경우 벡터 데이터베이스에 추가
        if rag_service and food_count > 0:
            # CSV에서 데이터 읽기
            df = pd.read_csv(processed_csv)

            start_time = time.time()
            doc_count = 0

            # 각 레코드를 RAG 문서로 변환하여 추가
            for _, row in df.iterrows():
                food_data = row.to_dict()

                # 태그 처리
                if "tags" in food_data and isinstance(food_data["tags"], str):
                    try:
                        food_data["tags"] = json.loads(food_data["tags"])
                    except:
                        tags_str = food_data["tags"]
                        food_data["tags"] = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
                else:
                    food_data["tags"] = []

                # RAG 문서로 변환
                rag_doc = data_processor.convert_food_data_to_rag_document(food_data)

                # 문서 추가
                if rag_service.add_documents([rag_doc]) > 0:
                    doc_count += 1

            rag_time = time.time() - start_time
            logger.info(f"RAG 문서 추가 완료. {doc_count}개 문서, 소요 시간: {rag_time:.2f}초")

        total_time = preprocess_time + import_time + (rag_time if rag_service else 0)
        logger.info(f"식품 CSV 파일 처리 및 임포트 완료. 총 소요 시간: {total_time:.2f}초")

        return food_count

    except Exception as e:
        logger.error(f"식품 CSV 파일 처리 및 임포트 오류: {str(e)}")
        return 0

def import_nutrition_articles(articles_dir: str, services: Dict[str, Any]) -> int:
    """
    영양 관련 문서 임포트 태스크

    Args:
        articles_dir (str): 문서 디렉토리 경로
        services (Dict[str, Any]): 서비스 객체들

    Returns:
        int: 임포트된 문서 수
    """
    try:
        logger.info(f"영양 관련 문서 임포트 시작: {articles_dir}")

        rag_service = services.get("rag_service")

        if not rag_service:
            logger.error("RAG 서비스가 초기화되지 않았습니다.")
            return 0

        if not os.path.exists(articles_dir) or not os.path.isdir(articles_dir):
            logger.error(f"문서 디렉토리가 존재하지 않습니다: {articles_dir}")
            return 0

        # 지원하는 파일 확장자
        supported_extensions = ['.txt', '.md', '.json']

        # 문서 파일 찾기
        article_files = []
        for ext in supported_extensions:
            article_files.extend(list(Path(articles_dir).glob(f'*{ext}')))

        if not article_files:
            logger.warning(f"임포트할 문서 파일이 없습니다: {articles_dir}")
            return 0

        # 문서 임포트
        doc_count = 0
        for file_path in article_files:
            try:
                file_ext = file_path.suffix.lower()

                # 파일 타입에 따라 처리
                if file_ext == '.json':
                    # JSON 파일 처리
                    with open(file_path, 'r', encoding='utf-8') as f:
                        articles = json.load(f)

                    if isinstance(articles, list):
                        for article in articles:
                            content = article.get('content', '')
                            title = article.get('title', 'Untitled')
                            source = article.get('source', str(file_path))

                            doc = {
                                "content": f"제목: {title}\n\n{content}",
                                "metadata": {
                                    "type": "nutrition_article",
                                    "title": title,
                                    "source": source,
                                    "added_at": datetime.now().isoformat()
                                }
                            }

                            if rag_service.add_documents([doc]) > 0:
                                doc_count += 1

                else:
                    # 텍스트 파일 처리
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # 제목 추출 (파일명 사용)
                    title = file_path.stem

                    doc = {
                        "content": f"제목: {title}\n\n{content}",
                        "metadata": {
                            "type": "nutrition_article",
                            "title": title,
                            "source": str(file_path),
                            "added_at": datetime.now().isoformat()
                        }
                    }

                    if rag_service.add_documents([doc]) > 0:
                        doc_count += 1

            except Exception as e:
                logger.error(f"문서 파일 처리 오류: {file_path}, {str(e)}")

        logger.info(f"영양 관련 문서 임포트 완료. {doc_count}개 문서 추가됨")
        return doc_count

    except Exception as e:
        logger.error(f"영양 관련 문서 임포트 오류: {str(e)}")
        return 0

def synchronize_food_database_to_rag(services: Dict[str, Any], batch_size: int = 100) -> int:
    """
    식품 데이터베이스와 RAG 벡터 데이터베이스 동기화 태스크

    Args:
        services (Dict[str, Any]): 서비스 객체들
        batch_size (int): 배치 크기

    Returns:
        int: 동기화된 문서 수
    """
    try:
        logger.info("식품 데이터베이스와 RAG 벡터 데이터베이스 동기화 시작")

        food_db = services.get("food_database")
        data_processor = services.get("data_processor")
        rag_service = services.get("rag_service")

        if not food_db or not data_processor or not rag_service:
            logger.error("필요한 서비스가 초기화되지 않았습니다.")
            return 0

        # 모든 식품 데이터 가져오기
        import sqlite3
        conn = sqlite3.connect("database/food_database.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 총 레코드 수 확인
        cursor.execute("SELECT COUNT(*) FROM foods")
        total_count = cursor.fetchone()[0]

        sync_count = 0
        batches = (total_count + batch_size - 1) // batch_size  # 올림 나눗셈

        for batch in range(batches):
            offset = batch * batch_size
            cursor.execute(f"SELECT * FROM foods LIMIT {batch_size} OFFSET {offset}")
            foods = [dict(row) for row in cursor.fetchall()]

            batch_docs = []
            for food in foods:
                # 태그 파싱
                if "tags" in food and food["tags"]:
                    try:
                        food["tags"] = json.loads(food["tags"])
                    except:
                        food["tags"] = []
                else:
                    food["tags"] = []

                # RAG 문서로 변환
                rag_doc = data_processor.convert_food_data_to_rag_document(food)
                batch_docs.append(rag_doc)

            # 배치 문서 추가
            if batch_docs:
                added = rag_service.add_documents(batch_docs)
                sync_count += added
                logger.info(f"배치 {batch+1}/{batches} 동기화 완료: {added}개 문서 추가됨")

        conn.close()

        logger.info(f"식품 데이터베이스와 RAG 벡터 데이터베이스 동기화 완료. {sync_count}개 문서 동기화됨")
        return sync_count

    except Exception as e:
        logger.error(f"데이터베이스 동기화 오류: {str(e)}")
        return 0

def create_sample_food_data_csv(output_path: str = "database/default_data/korean_foods.csv") -> str:
    """
    샘플 식품 데이터 CSV 파일 생성 태스크

    Args:
        output_path (str): 출력 파일 경로

    Returns:
        str: 생성된 CSV 파일 경로
    """
    try:
        logger.info(f"샘플 식품 데이터 CSV 파일 생성 시작: {output_path}")

        # 디렉토리 생성
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 샘플 데이터
        sample_foods = [
            {"name": "김치찌개", "category": "국/찌개", "calories": 250, "carbs": 10, "protein": 15, "fat": 12, "sodium": 1200, "fiber": 3, "sugar": 4, "tags": ["Korean", "spicy", "hot"], "description": "김치와 돼지고기를 넣고 끓인 한국의 전통 찌개"},
            {"name": "불고기", "category": "육류", "calories": 400, "carbs": 10, "protein": 30, "fat": 25, "sodium": 800, "fiber": 1, "sugar": 8, "tags": ["Korean", "beef", "grilled"], "description": "달콤한 양념에 재운 소고기를 구운 한국 요리"},
            {"name": "비빔밥", "category": "밥류", "calories": 600, "carbs": 80, "protein": 20, "fat": 15, "sodium": 900, "fiber": 5, "sugar": 6, "tags": ["Korean", "rice", "mixed"], "description": "밥 위에 여러 가지 나물과 고기를 올리고 고추장을 넣어 비벼 먹는 영양식"},
            {"name": "김치", "category": "반찬", "calories": 30, "carbs": 6, "protein": 1, "fat": 0.2, "sodium": 500, "fiber": 2, "sugar": 3, "tags": ["Korean", "fermented", "spicy"], "description": "배추를 소금에 절여 양념과 함께 발효시킨 한국의 대표적인 발효 식품"},
            {"name": "떡볶이", "category": "분식", "calories": 450, "carbs": 80, "protein": 8, "fat": 12, "sodium": 1100, "fiber": 2, "sugar": 15, "tags": ["Korean", "spicy", "rice cake"], "description": "떡과 고추장 소스를 매콤하게 볶은 한국의 대표적인 분식"},
            {"name": "라면", "category": "면류", "calories": 500, "carbs": 70, "protein": 10, "fat": 20, "sodium": 1800, "fiber": 1, "sugar": 2, "tags": ["Korean", "noodle", "instant"], "description": "끓는 물에 면과 스프를 넣어 조리하는 한국의 대표적인 인스턴트 식품"},
            {"name": "김밥", "category": "분식", "calories": 350, "carbs": 65, "protein": 10, "fat": 8, "sodium": 700, "fiber": 3, "sugar": 5, "tags": ["Korean", "rice", "seaweed"], "description": "김으로 밥과 다양한 재료를 말아 만든 한국의 대표적인 간편식"},
            {"name": "삼겹살", "category": "육류", "calories": 500, "carbs": 0, "protein": 25, "fat": 42, "sodium": 600, "fiber": 0, "sugar": 0, "tags": ["Korean", "pork", "grilled"], "description": "돼지고기 배를 잘라낸 부위로, 기름이 세 겹으로 층을 이루고 있어 구웠을 때 맛이 좋음"},
            {"name": "치킨", "category": "육류", "calories": 450, "carbs": 15, "protein": 35, "fat": 30, "sodium": 1000, "fiber": 0, "sugar": 1, "tags": ["Korean", "chicken", "fried"], "description": "튀김옷을 입혀 바삭하게 튀긴 닭고기 요리로 한국에서 인기 있는 외식 메뉴"},
            {"name": "된장찌개", "category": "국/찌개", "calories": 200, "carbs": 8, "protein": 12, "fat": 10, "sodium": 1000, "fiber": 4, "sugar": 2, "tags": ["Korean", "soybean", "traditional"], "description": "된장을 풀어 두부, 채소 등을 넣고 끓인 한국의 전통 찌개"},
            {"name": "갈비탕", "category": "국/찌개", "calories": 350, "carbs": 10, "protein": 28, "fat": 22, "sodium": 900, "fiber": 1, "sugar": 2, "tags": ["Korean", "beef", "soup"], "description": "소갈비를 넣고 푹 끓인 한국의 전통 탕 요리"},
            {"name": "냉면", "category": "면류", "calories": 480, "carbs": 85, "protein": 15, "fat": 5, "sodium": 1200, "fiber": 3, "sugar": 6, "tags": ["Korean", "noodle", "cold"], "description": "차가운 국물에 메밀면을 말아 먹는 한국의 여름 대표 음식"},
            {"name": "잡채", "category": "반찬", "calories": 320, "carbs": 45, "protein": 10, "fat": 15, "sodium": 600, "fiber": 4, "sugar": 8, "tags": ["Korean", "noodle", "vegetables"], "description": "당면과 여러 가지 채소, 고기를 함께 볶은 한국의 명절 음식"},
            {"name": "돈까스", "category": "육류", "calories": 550, "carbs": 40, "protein": 25, "fat": 35, "sodium": 700, "fiber": 2, "sugar": 3, "tags": ["Japanese", "pork", "fried"], "description": "돼지고기를 넓게 펴서 빵가루를 묻혀 튀긴 일본식 요리로 한국에서도 인기 있음"},
            {"name": "제육볶음", "category": "육류", "calories": 450, "carbs": 15, "protein": 30, "fat": 28, "sodium": 850, "fiber": 2, "sugar": 10, "tags": ["Korean", "pork", "spicy"], "description": "돼지고기를 매콤한 양념으로 볶은 한국의 대표적인 반찬"},
        ]

        # DataFrame 생성 및 CSV 저장
        df = pd.DataFrame(sample_foods)

        # 태그 직렬화
        df["tags"] = df["tags"].apply(lambda x: json.dumps(x, ensure_ascii=False))

        # CSV 저장
        df.to_csv(output_path, index=False, encoding='utf-8')

        logger.info(f"샘플 식품 데이터 CSV 파일 생성 완료: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"샘플 데이터 생성 오류: {str(e)}")
        return ""

def create_sample_recipes_json(output_path: str = "database/default_data/korean_recipes.json") -> str:
    """
    샘플 레시피 JSON 파일 생성 태스크

    Args:
        output_path (str): 출력 파일 경로

    Returns:
        str: 생성된 JSON 파일 경로
    """
    try:
        logger.info(f"샘플 레시피 JSON 파일 생성 시작: {output_path}")

        # 디렉토리 생성
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 샘플 레시피
        sample_recipes = [
            {
                "title": "건강한 비빔밥",
                "ingredients": ["현미밥", "시금치나물", "콩나물", "당근", "소고기", "계란", "참기름", "고추장"],
                "instructions": "1. 현미밥을 그릇에 담습니다.\n2. 준비된 나물과 고기를 올립니다.\n3. 계란 프라이를 올립니다.\n4. 고추장과 참기름을 넣고 비벼 먹습니다.",
                "calories": 550,
                "protein": 25,
                "fat": 15,
                "carbs": 70,
                "time": 25,
                "difficulty": "쉬움",
                "tags": ["Korean", "healthy", "balanced"],
                "health_goals": ["체중 관리", "근육 증가"]
            },
            {
                "title": "저탄수화물 닭가슴살 샐러드",
                "ingredients": ["닭가슴살", "로메인 상추", "방울토마토", "오이", "올리브 오일", "레몬즙", "소금", "후추"],
                "instructions": "1. 닭가슴살을 익혀 썰어둡니다.\n2. 채소를 씻어 먹기 좋게 썹니다.\n3. 올리브 오일, 레몬즙, 소금, 후추로 드레싱을 만듭니다.\n4. 모든 재료를 섞어 드레싱과 함께 즐깁니다.",
                "calories": 250,
                "protein": 35,
                "fat": 10,
                "carbs": 5,
                "time": 20,
                "difficulty": "쉬움",
                "tags": ["low-carb", "high-protein", "salad"],
                "health_goals": ["체중 감량", "다이어트"]
            },
            {
                "title": "두부 스크램블",
                "ingredients": ["두부", "양파", "피망", "당근", "강황", "소금", "후추", "올리브 오일"],
                "instructions": "1. 두부를 으깨서 물기를 제거합니다.\n2. 야채를 잘게 썹니다.\n3. 올리브 오일을 두른 팬에 야채를 볶다가 두부를 넣습니다.\n4. 강황, 소금, 후추를 넣고 계란 스크램블처럼 볶아줍니다.",
                "calories": 180,
                "protein": 15,
                "fat": 10,
                "carbs": 8,
                "time": 15,
                "difficulty": "쉬움",
                "tags": ["vegetarian", "breakfast", "high-protein"],
                "health_goals": ["체중 감량", "채식"]
            },
            {
                "title": "김치찌개",
                "ingredients": ["김치", "돼지고기", "두부", "대파", "고춧가루", "간장", "다진 마늘", "소금", "들기름"],
                "instructions": "1. 돼지고기를 먼저 볶다가 김치를 넣고 같이 볶습니다.\n2. 물을 붓고 양념을 넣어 끓입니다.\n3. 김치가 익으면 두부와 대파를 넣고 조금 더 끓입니다.\n4. 들기름을 살짝 두르고 바로 불을 끕니다.",
                "calories": 350,
                "protein": 20,
                "fat": 25,
                "carbs": 15,
                "time": 30,
                "difficulty": "쉬움",
                "tags": ["Korean", "spicy", "hot", "soup"],
                "health_goals": ["맛있는 식사", "전통 음식"]
            },
            {
                "title": "연어 아보카도 샐러드",
                "ingredients": ["훈제 연어", "아보카도", "상추", "토마토", "적양파", "올리브 오일", "레몬즙", "딜"],
                "instructions": "1. 모든 채소를 썰어 그릇에 담습니다.\n2. 연어와 아보카도를 올립니다.\n3. 올리브 오일, 레몬즙, 딜로 드레싱을 만들어 뿌립니다.",
                "calories": 320,
                "protein": 25,
                "fat": 22,
                "carbs": 8,
                "time": 15,
                "difficulty": "쉬움",
                "tags": ["low-carb", "omega-3", "salad"],
                "health_goals": ["체중 관리", "심장 건강"]
            }
        ]

        # JSON 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sample_recipes, f, ensure_ascii=False, indent=2)

        logger.info(f"샘플 레시피 JSON 파일 생성 완료: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"샘플 레시피 생성 오류: {str(e)}")
        return ""

def create_sample_nutrition_articles(output_dir: str = "database/data/nutrition_articles") -> int:
    """
    샘플 영양 관련 문서 생성 태스크

    Args:
        output_dir (str): 출력 디렉토리 경로

    Returns:
        int: 생성된 문서 수
    """
    try:
        logger.info(f"샘플 영양 관련 문서 생성 시작: {output_dir}")

        # 디렉토리 생성
        os.makedirs(output_dir, exist_ok=True)

        # 샘플 문서 내용
        sample_articles = [
            {
                "title": "단백질의 중요성",
                "content": """단백질은 근육, 피부, 효소, 호르몬 등 우리 몸을 구성하는 필수적인 영양소입니다. 
                
단백질은 아미노산으로 구성되며, 이 중 9가지는 필수 아미노산으로 음식을 통해 섭취해야 합니다. 부족할 경우 근육량 감소, 면역력 저하, 피로감 등의 증상이 나타날 수 있습니다.

건강한 성인의 경우 체중 1kg당 약 0.8g의 단백질 섭취가 권장되지만, 운동량이 많거나 근육 증가를 원하는 경우 이보다 더 많은 양(1.6-2.2g/kg)이 필요할 수 있습니다.

양질의 단백질 공급원으로는 닭가슴살, 계란, 생선, 두부, 콩류 등이 있으며, 식물성 단백질과 동물성 단백질을 균형 있게 섭취하는 것이 좋습니다."""
            },
            {
                "title": "탄수화물의 역할과 선택",
                "content": """탄수화물은 우리 몸의 주요 에너지원으로, 뇌와 신경계의 기능을 유지하는 데 필수적입니다.

모든 탄수화물이 같지는 않습니다. 단순 탄수화물(설탕, 백미 등)은 혈당을 빠르게 올리고 내리게 하는 반면, 복합 탄수화물(현미, 통곡물, 채소 등)은 천천히 소화되어 지속적인 에너지를 제공합니다.

당뇨병이나 체중 관리를 위해서는 낮은 당지수(GI)를 가진 식품을 선택하는 것이 좋습니다. 이런 식품들은 혈당을 급격히 올리지 않고 포만감을 오래 유지해 줍니다.

식이섬유가 풍부한 탄수화물 식품은 소화를 돕고 장 건강을 증진시키며, 콜레스테롤 수치를 낮추는 데 도움이 됩니다."""
            },
            {
                "title": "한국 전통 식단의 영양학적 가치",
                "content": """한국 전통 식단은 영양학적으로 매우 균형 잡힌 식단으로 평가받고 있습니다.

한국의 전통적인 식사 구성인 '밥, 국, 반찬'은 탄수화물, 단백질, 지방, 비타민, 미네랄 등 필요한 영양소를 골고루 섭취할 수 있도록 설계되어 있습니다.

발효 식품인 김치, 된장, 간장, 고추장 등은 프로바이오틱스와 항산화 물질이 풍부하여 장 건강과 면역력 증진에 도움을 줍니다.

다양한 나물 반찬은 식이섬유와 비타민, 미네랄이 풍부하며, 육류와 생선, 두부 등의 단백질 식품과 균형을 이룹니다.

현대 연구에 따르면 한국 전통 식단은 비만, 당뇨병, 심혈관 질환 등 현대인의 생활습관병 예방에 효과적인 것으로 나타났습니다."""
            }
        ]

        # 문서 생성
        article_count = 0

        # 텍스트 파일로 저장
        for i, article in enumerate(sample_articles):
            file_path = os.path.join(output_dir, f"{i+1}_{article['title'].replace(' ', '_')}.txt")

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# {article['title']}\n\n")
                f.write(article['content'])

            article_count += 1

        # JSON 파일로도 저장
        json_path = os.path.join(output_dir, "nutrition_articles.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(sample_articles, f, ensure_ascii=False, indent=2)

        article_count += 1  # JSON 파일 포함

        logger.info(f"샘플 영양 관련 문서 생성 완료: {article_count}개 파일")
        return article_count

    except Exception as e:
        logger.error(f"샘플 문서 생성 오류: {str(e)}")
        return 0