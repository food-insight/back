import os
import logging
import json
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from datetime import datetime

class DataProcessorService:
    """데이터 처리 서비스"""

    def __init__(self, data_dir: str = "database/data"):
        """
        데이터 처리 서비스 초기화

        Args:
            data_dir (str): 데이터 디렉토리
        """
        self.logger = logging.getLogger(__name__)
        self.data_dir = data_dir

        # 디렉토리 생성
        os.makedirs(data_dir, exist_ok=True)

    def process_food_csv(self, csv_path: str, output_path: Optional[str] = None) -> str:
        """
        식품 CSV 파일 처리

        Args:
            csv_path (str): 원본 CSV 파일 경로
            output_path (Optional[str]): 출력 파일 경로

        Returns:
            str: 처리된 CSV 파일 경로
        """
        try:
            self.logger.info(f"식품 CSV 파일 처리 시작: {csv_path}")

            # CSV 파일 로드
            df = pd.read_csv(csv_path)

            # 컬럼명 정리 (공백 제거, 소문자 변환)
            df.columns = [col.strip().lower() for col in df.columns]

            # 필수 컬럼 확인 및 추가
            required_columns = ["name", "category", "calories", "carbs", "protein", "fat"]
            for col in required_columns:
                if col not in df.columns:
                    if col == "name" or col == "category":
                        raise ValueError(f"필수 컬럼이 없습니다: {col}")
                    else:
                        df[col] = 0

            # 결측치 처리
            numeric_columns = ["calories", "carbs", "protein", "fat", "sodium", "fiber", "sugar"]
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            # 문자열 컬럼 처리
            string_columns = ["name", "category", "description"]
            for col in string_columns:
                if col in df.columns:
                    df[col] = df[col].astype(str).replace('nan', '')

            # 태그 처리
            if "tags" in df.columns:
                # 문자열로 된 태그를 리스트로 변환
                df["tags"] = df["tags"].apply(lambda x: self._parse_tags(x) if pd.notna(x) else [])
            else:
                df["tags"] = [[]] * len(df)

            # 중복 제거
            df = df.drop_duplicates(subset=["name"])

            # 결과 저장
            if output_path is None:
                filename = os.path.basename(csv_path)
                base_name, ext = os.path.splitext(filename)
                output_path = os.path.join(self.data_dir, f"{base_name}_processed{ext}")

            df.to_csv(output_path, index=False)
            self.logger.info(f"식품 CSV 파일 처리 완료: {output_path}")

            return output_path

        except Exception as e:
            self.logger.error(f"식품 CSV 파일 처리 오류: {str(e)}")
            raise

    def _parse_tags(self, tags_str: Union[str, List]) -> List[str]:
        """
        태그 문자열 파싱

        Args:
            tags_str (Union[str, List]): 태그 문자열 또는 리스트

        Returns:
            List[str]: 태그 리스트
        """
        if isinstance(tags_str, list):
            return tags_str

        try:
            # JSON 형식으로 파싱 시도
            return json.loads(tags_str)
        except:
            # 쉼표로 구분된 문자열로 처리
            return [tag.strip() for tag in tags_str.split(',') if tag.strip()]

    def process_nutrition_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        영양 데이터 처리

        Args:
            data (Dict[str, Any]): 원본 영양 데이터

        Returns:
            Dict[str, Any]: 처리된 영양 데이터
        """
        try:
            self.logger.info("영양 데이터 처리 시작")

            processed_data = {}

            # 기본 필드 복사
            for key in ["name", "category", "description"]:
                processed_data[key] = data.get(key, "")

            # 숫자 필드 처리
            numeric_fields = [
                "calories", "carbs", "protein", "fat",
                "sodium", "fiber", "sugar"
            ]

            for field in numeric_fields:
                value = data.get(field, 0)
                try:
                    processed_data[field] = float(value)
                except:
                    processed_data[field] = 0.0

            # 태그 처리
            tags = data.get("tags", [])
            if isinstance(tags, str):
                processed_data["tags"] = self._parse_tags(tags)
            else:
                processed_data["tags"] = list(tags)

            # 추가 계산 필드
            processed_data["calories_per_gram"] = self._calculate_calories_per_gram(processed_data)
            processed_data["protein_per_calorie"] = self._calculate_protein_per_calorie(processed_data)

            self.logger.info("영양 데이터 처리 완료")
            return processed_data

        except Exception as e:
            self.logger.error(f"영양 데이터 처리 오류: {str(e)}")
            return data

    def _calculate_calories_per_gram(self, data: Dict[str, Any]) -> float:
        """
        그램당 칼로리 계산

        Args:
            data (Dict[str, Any]): 영양 데이터

        Returns:
            float: 그램당 칼로리
        """
        total_weight = data.get("carbs", 0) + data.get("protein", 0) + data.get("fat", 0)
        if total_weight > 0:
            return data.get("calories", 0) / total_weight
        return 0

    def _calculate_protein_per_calorie(self, data: Dict[str, Any]) -> float:
        """
        칼로리당 단백질 계산

        Args:
            data (Dict[str, Any]): 영양 데이터

        Returns:
            float: 칼로리당 단백질
        """
        calories = data.get("calories", 0)
        if calories > 0:
            return data.get("protein", 0) / calories
        return 0

    def convert_food_data_to_rag_document(self, food_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        식품 데이터를 RAG 문서로 변환

        Args:
            food_data (Dict[str, Any]): 식품 데이터

        Returns:
            Dict[str, Any]: RAG 문서
        """
        try:
            name = food_data.get("name", "Untitled")
            self.logger.info(f"식품 데이터를 RAG 문서로 변환: {name}")

            # 문서 내용 생성
            content = f"""
식품명: {name}
카테고리: {food_data.get('category', '기타')}
영양정보:
- 칼로리: {food_data.get('calories', 0)}kcal
- 탄수화물: {food_data.get('carbs', 0)}g
- 단백질: {food_data.get('protein', 0)}g
- 지방: {food_data.get('fat', 0)}g
- 나트륨: {food_data.get('sodium', 0)}mg
- 식이섬유: {food_data.get('fiber', 0)}g
- 당류: {food_data.get('sugar', 0)}g

태그: {', '.join(food_data.get('tags', []))}

설명: {food_data.get('description', '')}

건강 정보:
이 음식은 {'저칼로리 음식입니다.' if food_data.get('calories', 0) < 200 else '고칼로리 음식입니다.'}
단백질 함량이 {'높습니다.' if food_data.get('protein', 0) > 15 else '보통입니다.' if food_data.get('protein', 0) > 5 else '낮습니다.'}
"""

            # 메타데이터 생성
            metadata = {
                "type": "food",
                "name": name,
                "category": food_data.get('category', '기타'),
                "calories": food_data.get('calories', 0),
                "protein": food_data.get('protein', 0),
                "converted_at": datetime.now().isoformat()
            }

            return {
                "content": content,
                "metadata": metadata
            }

        except Exception as e:
            self.logger.error(f"RAG 문서 변환 오류: {str(e)}")
            return {
                "content": "",
                "metadata": {}
            }