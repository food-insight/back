import os
import json
import logging
import pandas as pd
import sqlite3
from typing import List, Dict, Any, Optional
from pathlib import Path

class FoodDatabaseService:
    """식품 데이터베이스 관리 서비스"""

    def get_similar_foods(self, food_name: str, category: str, limit: int = 5) -> List[Dict[str, Any]]:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # 기준 음식의 칼로리를 조회
            cursor.execute("SELECT calories FROM foods WHERE name = ?", (food_name,))
            row = cursor.fetchone()
            if not row:
                return []
            base_calories = row["calories"]

            # 같은 카테고리 내에서 기준 음식과 칼로리 차이를 기준으로 정렬
            cursor.execute("""
                SELECT *, ABS(calories - ?) as calorie_diff
                FROM foods
                WHERE category = ? AND name != ?
                ORDER BY calorie_diff ASC
                LIMIT ?
            """, (base_calories, category, food_name, limit))
            rows = cursor.fetchall()
            similar_foods = []
            for row in rows:
                food = dict(row)
                food["tags"] = json.loads(food["tags"]) if food["tags"] else []
                similar_foods.append(food)
            return similar_foods
        except Exception as e:
            self.logger.error(f"유사 음식 검색 오류: {str(e)}")
            return []
        finally:
            try:
                conn.close()
            except Exception:
                pass
        

    def __init__(self, db_path: str = "database/food_database.db"):
        """
        식품 데이터베이스 서비스 초기화

        Args:
            db_path (str): 데이터베이스 파일 경로
        """
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path

        # 디렉토리 생성
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # 데이터베이스 초기화
        self._init_database()

    def is_initialized(self) -> bool:
        """ 데이터베이스 파일이 존재하는지 확인 """
        return os.path.exists(self.db_path)

    def _init_database(self):
        """데이터베이스 스키마 초기화"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 식품 테이블 생성
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS foods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                category TEXT,
                calories REAL,
                carbs REAL,
                protein REAL,
                fat REAL,
                sodium REAL,
                fiber REAL,
                sugar REAL,
                tags TEXT,
                description TEXT,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # 레시피 테이블 생성
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL UNIQUE,
                ingredients TEXT NOT NULL,
                instructions TEXT NOT NULL,
                calories REAL,
                carbs REAL,
                protein REAL,
                fat REAL,
                time INTEGER,
                difficulty TEXT,
                tags TEXT,
                health_goals TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            conn.commit()
            conn.close()
            self.logger.info("데이터베이스 스키마 초기화 완료")

        except Exception as e:
            self.logger.error(f"데이터베이스 초기화 오류: {str(e)}")
            raise

    def import_food_data_from_csv(self, csv_path: str, batch_size: int = 100) -> int:
        """
        CSV 파일에서 식품 데이터 가져오기

        Args:
            csv_path (str): CSV 파일 경로
            batch_size (int): 배치 처리 크기

        Returns:
            int: 임포트된 식품 데이터 수
        """
        try:
            self.logger.info(f"CSV에서 식품 데이터 가져오기 시작: {csv_path}")

            # CSV 파일 읽기
            df = pd.read_csv(csv_path)

            # 필수 컬럼 확인
            required_columns = ["name", "category", "calories"]
            for col in required_columns:
                if col not in df.columns:
                    raise ValueError(f"CSV 파일에 필수 컬럼이 없습니다: {col}")

            # 데이터 정제
            df = self._clean_food_data(df)

            # 배치 처리
            total_records = 0
            conn = sqlite3.connect(self.db_path)

            for i in range(0, len(df), batch_size):
                batch_df = df.iloc[i:i+batch_size]
                batch_records = []

                for _, row in batch_df.iterrows():
                    record = {
                        "name": row["name"],
                        "category": row.get("category", "기타"),
                        "calories": row.get("calories", 0),
                        "carbs": row.get("carbs", 0),
                        "protein": row.get("protein", 0),
                        "fat": row.get("fat", 0),
                        "sodium": row.get("sodium", 0),
                        "fiber": row.get("fiber", 0),
                        "sugar": row.get("sugar", 0),
                        "tags": self._serialize_list(row.get("tags", [])),
                        "description": row.get("description", ""),
                        "source": csv_path
                    }
                    batch_records.append(record)

                # 데이터베이스에 배치 삽입
                self._insert_food_batch(conn, batch_records)
                total_records += len(batch_records)
                self.logger.info(f"식품 데이터 {total_records}/{len(df)} 임포트 완료")

            conn.close()
            self.logger.info(f"총 {total_records}개의 식품 데이터 가져오기 완료")
            return total_records

        except Exception as e:
            self.logger.error(f"CSV 데이터 가져오기 오류: {str(e)}")
            return 0

    def _clean_food_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        식품 데이터 정제

        Args:
            df (pd.DataFrame): 원본 데이터프레임

        Returns:
            pd.DataFrame: 정제된 데이터프레임
        """
        # 결측치 처리
        for col in ["calories", "carbs", "protein", "fat", "sodium", "fiber", "sugar"]:
            if col in df.columns:
                df[col] = df[col].fillna(0)

        # 문자열 컬럼 처리
        for col in ["name", "category", "description"]:
            if col in df.columns:
                df[col] = df[col].fillna("")

        # 중복 제거
        df = df.drop_duplicates(subset=["name"])

        return df

    def _insert_food_batch(self, conn: sqlite3.Connection, records: List[Dict[str, Any]]):
        """
        식품 데이터 배치 삽입

        Args:
            conn (sqlite3.Connection): 데이터베이스 연결
            records (List[Dict[str, Any]]): 삽입할 레코드
        """
        cursor = conn.cursor()

        for record in records:
            try:
                cursor.execute('''
                INSERT OR REPLACE INTO foods
                (name, category, calories, carbs, protein, fat, sodium, fiber, sugar, tags, description, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record["name"],
                    record["category"],
                    record["calories"],
                    record["carbs"],
                    record["protein"],
                    record["fat"],
                    record["sodium"],
                    record["fiber"],
                    record["sugar"],
                    record["tags"],
                    record["description"],
                    record["source"]
                ))
            except Exception as e:
                self.logger.error(f"레코드 삽입 오류: {record['name']}, {str(e)}")

        conn.commit()

    def _serialize_list(self, list_data: Any) -> str:
        """
        리스트 데이터를 직렬화

        Args:
            list_data (Any): 직렬화할 리스트

        Returns:
            str: 직렬화된 문자열
        """
        if isinstance(list_data, list):
            return json.dumps(list_data, ensure_ascii=False)
        elif isinstance(list_data, str):
            return list_data
        else:
            return json.dumps([], ensure_ascii=False)

    def _safe_json_loads(self, json_str, default=None):
        """
        안전하게 JSON 문자열을 파싱하는 헬퍼 메소드

        Args:
            json_str: 파싱할 JSON 문자열
            default: 파싱 실패 시 반환할 기본값

        Returns:
            파싱된 객체 또는 기본값
        """
        if not json_str:
            return default if default is not None else []

        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            self.logger.warning(f"JSON 파싱 실패: {json_str[:50]}...")
            return default if default is not None else []

    def get_food_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        이름으로 식품 정보 조회

        Args:
            name (str): 식품 이름

        Returns:
            Optional[Dict[str, Any]]: 식품 정보
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM foods WHERE name = ?", (name,))
            row = cursor.fetchone()

            if row:
                food = dict(row)
                food["tags"] = self._safe_json_loads(food["tags"])
                return food

            return None

        except Exception as e:
            self.logger.error(f"식품 조회 오류: {str(e)}")
            return None
        finally:
            if conn:
                conn.close()

    def get_all_foods(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        모든 식품 정보 조회

        Args:
            limit (int): 반환할 최대 항목 수

        Returns:
            List[Dict[str, Any]]: 식품 정보 목록
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM foods LIMIT ?", (limit,))
            rows = cursor.fetchall()

            foods = []
            for row in rows:
                food = dict(row)
                food["tags"] = self._safe_json_loads(food["tags"])
                foods.append(food)

            return foods

        except Exception as e:
            self.logger.error(f"모든 식품 조회 오류: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()

    def get_similar_foods(self, food_name: str, category: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        유사한 식품 검색

        Args:
            food_name (str): 기준 식품 이름
            category (Optional[str]): 카테고리
            limit (int): 최대 결과 수

        Returns:
            List[Dict[str, Any]]: 유사 식품 목록
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = "SELECT * FROM foods WHERE name != ?"
            params = [food_name]

            if category:
                query += " AND category = ?"
                params.append(category)

            query += " LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            similar_foods = []
            for row in rows:
                food = dict(row)
                food["tags"] = self._safe_json_loads(food["tags"])
                similar_foods.append(food)

            return similar_foods

        except Exception as e:
            self.logger.error(f"유사 식품 검색 오류: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()

    def search_foods(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        식품 검색

        Args:
            query (str): 검색어
            limit (int): 최대 결과 수

        Returns:
            List[Dict[str, Any]]: 검색 결과
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
            SELECT * FROM foods 
            WHERE name LIKE ? OR category LIKE ? OR description LIKE ? OR tags LIKE ?
            LIMIT ?
            """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", limit))

            rows = cursor.fetchall()

            foods = []
            for row in rows:
                food = dict(row)
                food["tags"] = self._safe_json_loads(food["tags"])
                foods.append(food)

            return foods

        except Exception as e:
            self.logger.error(f"식품 검색 오류: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()