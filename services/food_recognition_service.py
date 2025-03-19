import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import numpy as np
import random
from werkzeug.utils import secure_filename
from services.food_database import FoodDatabaseService
from services.rag_service import RAGService
from dotenv import load_dotenv


class FoodRecognitionService:
    """
    음식 인식 및 분석 서비스
    """
    def __init__(self, food_db=None, rag_service=None):
        """
        음식 인식 서비스 초기화

        Args:
            food_db (Optional[FoodDatabaseService]): 식품 데이터베이스 서비스
            rag_service (Optional[RAGService]): RAG 서비스
        """
        self.logger = logging.getLogger(__name__)

        # 환경 변수 로드
        load_dotenv()
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            self.logger.error("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

        self.food_db = food_db or FoodDatabaseService()
        self.rag_service = rag_service or RAGService(openai_api_key=openai_api_key)

        # 샘플 음식 데이터 (모델이 실제로 구현되기 전까지 사용)
        # 실제 구현에서는 ML 모델을 통해 이미지 인식 수행
        self.SAMPLE_FOODS = [
            {"name": "김치찌개", "confidence": 0.92, "category": "국/찌개"},
            {"name": "불고기", "confidence": 0.88, "category": "육류"},
            {"name": "된장찌개", "confidence": 0.85, "category": "국/찌개"},
            {"name": "비빔밥", "confidence": 0.90, "category": "밥류"},
            {"name": "삼겹살", "confidence": 0.93, "category": "육류"},
            {"name": "김치", "confidence": 0.95, "category": "반찬"},
            {"name": "떡볶이", "confidence": 0.94, "category": "분식"},
            {"name": "라면", "confidence": 0.92, "category": "면류"},
            {"name": "김밥", "confidence": 0.89, "category": "분식"},
            {"name": "치킨", "confidence": 0.91, "category": "육류"}
        ]

    def recognize_food_from_image(self, image_data):
        """
        이미지에서 음식 인식 수행

        Args:
            image_data: 이미지 데이터(바이너리 또는 파일 경로)

        Returns:
            list: 인식된 식품 목록과 신뢰도 점수
        """
        try:
            self.logger.info("이미지에서 음식 인식 시작")

            # 이미지 경로인 경우
            if isinstance(image_data, str) and os.path.exists(image_data):
                image_path = image_data
            # 바이너리 데이터인 경우 임시 파일로 저장
            elif isinstance(image_data, bytes):
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                    tmp.write(image_data)
                    image_path = tmp.name
            else:
                self.logger.error("지원되지 않는 이미지 데이터 형식")
                return []

            # 여기서는 이미지 인식 로직 구현
            # 실제 프로젝트에서는 외부 API나 ML 모델을 사용할 수 있음

            # 이미지 로드 및 전처리
            try:
                image = Image.open(image_path)
                self.logger.info(f"이미지 로드 성공: {image.size}px, {image.mode}")

                # 임시 파일인 경우 삭제
                if isinstance(image_data, bytes) and os.path.exists(image_path):
                    os.unlink(image_path)

            except Exception as e:
                self.logger.error(f"이미지 로드 실패: {str(e)}")
                return []

            # 이미지에 따라 1~3개의 음식 감지 (랜덤으로 시뮬레이션)
            detected_count = random.randint(1, 3)
            recognized_foods = random.sample(self.SAMPLE_FOODS, detected_count)

            # 인식된 식품에 대한 추가 정보 조회
            enriched_foods = []
            for food in recognized_foods:
                food_info = self.food_db.get_food_by_name(food["name"])
                if food_info:
                    food["details"] = food_info
                    food["source"] = "database"
                else:
                    # 데이터베이스에 없는 경우 RAG 시스템 활용
                    rag_info = self.rag_service.query_food_info(f"{food['name']}의 정보")
                    food["details"] = {"description": rag_info}
                    food["source"] = "rag"
                enriched_foods.append(food)

            self.logger.info(f"음식 인식 완료: {detected_count}개 감지됨")
            return enriched_foods

        except Exception as e:
            self.logger.error(f"음식 인식 중 오류 발생: {str(e)}")
            return []

    def recognize_food_from_text(self, text_description):
        """
        텍스트 설명에서 식품을 인식하는 메소드

        Args:
            text_description: 식품에 대한 텍스트 설명

        Returns:
            list: 인식된 식품 목록
        """
        try:
            self.logger.info(f"텍스트에서 음식 이름 추출 시작")

            # RAG 시스템을 사용하여 텍스트에서 식품 식별
            # 실제 구현에서는 RAG 시스템이나 NER 모델을 사용할 수 있음
            # 여기서는 간단한 구현으로 대체

            # 흔한 한국 음식 목록
            korean_foods = [
                "김치", "불고기", "비빔밥", "떡볶이", "김밥", "라면", "삼겹살", "치킨",
                "된장찌개", "김치찌개", "순두부찌개", "갈비탕", "설렁탕", "불고기", "갈비",
                "잡채", "잔치국수", "냉면", "만두", "제육볶음", "닭갈비", "돼지갈비",
                "김치볶음밥", "오므라이스", "돈까스", "감자탕", "부대찌개", "보쌈", "족발"
            ]

            # 식별된 식품에 대한 정보 조회
            food_candidates = [food for food in korean_foods if food in text_description]
            food_candidates = list(set(food_candidates))  # 중복 제거

            # RAG 시스템 활용 시도
            try:
                rag_foods = self.rag_service.extract_food_entities(text_description)
                if rag_foods:
                    # RAG로 추출한 음식명과 기존 목록 병합
                    food_candidates = list(set(food_candidates + rag_foods))
            except Exception as e:
                self.logger.warning(f"RAG 시스템에서 음식 추출 중 오류: {str(e)}")

            enriched_foods = []
            for food_name in food_candidates:
                food_info = self.food_db.get_food_by_name(food_name)
                if food_info:
                    enriched_foods.append({
                        "name": food_name,
                        "details": food_info,
                        "source": "database",
                        "confidence": 0.9  # 확신도는 실제 구현에서 계산 필요
                    })
                else:
                    # 데이터베이스에 없는 경우
                    rag_info = self.rag_service.query_food_info(f"{food_name}의 정보")
                    enriched_foods.append({
                        "name": food_name,
                        "details": {"description": rag_info},
                        "source": "rag",
                        "confidence": 0.7  # RAG 기반 결과는 일반적으로 확신도가 낮을 수 있음
                    })

            self.logger.info(f"텍스트에서 음식 이름 추출 완료: {len(enriched_foods)}개 감지됨")
            return enriched_foods

        except Exception as e:
            self.logger.error(f"텍스트에서 음식 이름 추출 중 오류 발생: {str(e)}")
            return []

    def process_food_image(self, image_path: str) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        음식 이미지 처리 및 분석
        """
        try:
            # 이미지 처리 (resize, enhance 등)
            processed_path = self.enhance_image_quality(image_path)

            # 음식 인식
            recognized_foods = self.recognize_food_from_image(processed_path or image_path)

            return recognized_foods, processed_path
        except Exception as e:
            self.logger.error(f"음식 이미지 처리 및 분석 중 오류 발생: {str(e)}")
            return [], None

    def enhance_image_quality(self, image_path: str) -> Optional[str]:
        """
        이미지 품질 개선
        """
        try:
            # 원본 이미지 로드
            img = Image.open(image_path)

            # 이미지 크기 조정 (최대 1000x1000 제한)
            max_size = 1000
            if img.width > max_size or img.height > max_size:
                # 비율 유지하면서 크기 조정
                ratio = min(max_size / img.width, max_size / img.height)
                new_width = int(img.width * ratio)
                new_height = int(img.height * ratio)
                img = img.resize((new_width, new_height), Image.LANCZOS)

            # 품질 개선 (간단한 예시)
            from PIL import ImageEnhance

            # 명암 개선
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.2)

            # 선명도 개선
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.3)

            # 밝기 조정
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.1)

            # 결과 저장
            file_name = os.path.basename(image_path)
            base_name, ext = os.path.splitext(file_name)
            processed_path = os.path.join(
                os.path.dirname(image_path),
                f"{base_name}_processed{ext}"
            )

            img.save(processed_path, quality=90)
            self.logger.info(f"이미지 품질 개선 완료: {processed_path}")

            return processed_path
        except Exception as e:
            self.logger.error(f"이미지 품질 개선 중 오류 발생: {str(e)}")
            return None

    def get_food_details(self, food_name: str) -> Dict[str, Any]:
        """
        음식 상세 정보 조회
        """
        try:
            # 데이터베이스에서 음식 정보 조회
            food_info = self.food_db.get_food_by_name(food_name)

            if food_info:
                return {
                    "name": food_name,
                    "details": food_info,
                    "source": "database"
                }
            else:
                # 데이터베이스에 없는 경우 RAG 시스템 활용
                rag_info = self.rag_service.query_food_info(f"{food_name}의 상세 정보")
                return {
                    "name": food_name,
                    "details": {"description": rag_info},
                    "source": "rag"
                }

        except Exception as e:
            self.logger.error(f"음식 상세 정보 조회 중 오류 발생: {str(e)}")
            return {
                "name": food_name,
                "details": {"description": f"{food_name}에 대한 정보를 찾을 수 없습니다."},
                "source": "error"
            }