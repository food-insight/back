import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import numpy as np
import random
from werkzeug.utils import secure_filename

class FoodRecognitionService:
    """
    음식 인식 및 분석 서비스
    """
    def __init__(self, sample_foods=None):
        """
        음식 인식 서비스 초기화

        Args:
            sample_foods (Optional[List[Dict]]): 샘플 음식 데이터
        """
        self.logger = logging.getLogger(__name__)

        # 샘플 음식 데이터
        self.SAMPLE_FOODS = sample_foods or [
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

        # 샘플 영양 정보
        self.NUTRITION_INFO = {
            "김치찌개": {"calories": 250, "carbs": 10, "protein": 15, "fat": 12, "sodium": 1200},
            "불고기": {"calories": 400, "carbs": 10, "protein": 30, "fat": 25, "sodium": 800},
            "비빔밥": {"calories": 600, "carbs": 80, "protein": 20, "fat": 15, "sodium": 900},
            "김치": {"calories": 30, "carbs": 6, "protein": 1, "fat": 0.2, "sodium": 500},
            "떡볶이": {"calories": 450, "carbs": 80, "protein": 8, "fat": 12, "sodium": 1100},
            "라면": {"calories": 500, "carbs": 70, "protein": 10, "fat": 20, "sodium": 1800},
            "김밥": {"calories": 350, "carbs": 65, "protein": 10, "fat": 8, "sodium": 700},
            "삼겹살": {"calories": 500, "carbs": 0, "protein": 25, "fat": 42, "sodium": 600},
            "치킨": {"calories": 450, "carbs": 15, "protein": 35, "fat": 30, "sodium": 1000}
        }

    def recognize_food_from_image(self, image_path: str) -> List[Dict[str, Any]]:
        """
        이미지에서 음식 인식 수행
        """
        try:
            self.logger.info(f"이미지에서 음식 인식 시작: {image_path}")

            # 이미지 존재 및 파일 형식 확인
            if not os.path.exists(image_path):
                self.logger.error(f"이미지 파일이 존재하지 않습니다: {image_path}")
                return []

            # 이미지 로드 및 전처리
            try:
                image = Image.open(image_path)
                self.logger.info(f"이미지 로드 성공: {image.size}px, {image.mode}")
            except Exception as e:
                self.logger.error(f"이미지 로드 실패: {str(e)}")
                return []

            # 이미지에 따라 1~3개의 음식 감지 (랜덤으로 시뮬레이션)
            detected_count = random.randint(1, 3)
            detected_foods = random.sample(self.SAMPLE_FOODS, detected_count)

            self.logger.info(f"음식 인식 완료: {detected_count}개 감지됨")
            return detected_foods

        except Exception as e:
            self.logger.error(f"음식 인식 중 오류 발생: {str(e)}")
            return []

    def extract_food_names_from_text(self, text: str) -> List[str]:
        """
        텍스트에서 음식 이름 추출
        """
        try:
            self.logger.info(f"텍스트에서 음식 이름 추출 시작")

            # 흔한 한국 음식 목록
            korean_foods = [
                "김치", "불고기", "비빔밥", "떡볶이", "김밥", "라면", "삼겹살", "치킨",
                "된장찌개", "김치찌개", "순두부찌개", "갈비탕", "설렁탕", "불고기", "갈비",
                "잡채", "잔치국수", "냉면", "만두", "제육볶음", "닭갈비", "돼지갈비",
                "김치볶음밥", "오므라이스", "돈까스", "감자탕", "부대찌개", "보쌈", "족발"
            ]

            detected_foods = [
                food for food in korean_foods
                if food in text
            ]

            # 중복 제거
            detected_foods = list(set(detected_foods))

            self.logger.info(f"텍스트에서 음식 이름 추출 완료: {len(detected_foods)}개 감지됨")
            return detected_foods

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
        # 기본 음식 정보
        food_info = {
            "name": food_name,
            "nutrition": self.NUTRITION_INFO.get(food_name, {"calories": 300, "carbs": 30, "protein": 15, "fat": 10, "sodium": 500}),
            "category": next((food["category"] for food in self.SAMPLE_FOODS if food["name"] == food_name), "기타"),
            "description": f"{food_name}은 한국의 대표적인 음식입니다.",
            "ingredients": ["주 재료", "부재료", "양념"]
        }

        return food_info

def initialize_food_recognition_service() -> FoodRecognitionService:
    """
    음식 인식 서비스 초기화

    Returns:
        FoodRecognitionService: 초기화된 음식 인식 서비스
    """
    return FoodRecognitionService()