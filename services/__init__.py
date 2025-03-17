# services/__init__.py
from typing import Optional, Dict, Any

from .food_database import FoodDatabaseService
from .rag_service import RAGService
from .data_processor import DataProcessorService
from .nutrition_analysis import NutritionAnalysisService
from .food_recognition import FoodRecognitionService
from .recommendation import RecommendationService

class ServiceManager:
    """
    모든 서비스를 통합적으로 관리하는 매니저 클래스
    """
    _instance: Optional['ServiceManager'] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # 기본 서비스 초기화
        self.food_db: FoodDatabaseService = FoodDatabaseService()
        self.rag_service: RAGService = RAGService()
        self.data_processor: DataProcessorService = DataProcessorService(self.food_db, self.rag_service)

        # 기능 서비스 초기화 (의존성 주입)
        self.nutrition_analysis: NutritionAnalysisService = NutritionAnalysisService(self.food_db, self.rag_service)
        self.food_recognition: FoodRecognitionService = FoodRecognitionService(self.food_db, self.rag_service)
        self.recommendation: RecommendationService = RecommendationService(self.food_db, self.rag_service)

        self._initialized = True

    def initialize_databases(self, force_rebuild: bool = False) -> None:
        """
        데이터베이스와 벡터 저장소 초기화

        Args:
            force_rebuild: 강제로 데이터베이스 재구축 여부
        """
        # 식품 데이터베이스 초기화
        if force_rebuild or not self.food_db.is_initialized():
            self.food_db.initialize()

        # RAG 시스템 초기화
        if force_rebuild or not self.rag_service.is_initialized():
            self.rag_service.initialize()

    def get_service(self, service_name: str) -> Any:
        """
        서비스 이름으로 서비스 인스턴스 반환

        Args:
            service_name: 서비스 이름

        Returns:
            해당 서비스 인스턴스
        """
        services: Dict[str, Any] = {
            'food_db': self.food_db,
            'rag': self.rag_service,
            'data_processor': self.data_processor,
            'nutrition': self.nutrition_analysis,
            'recognition': self.food_recognition,
            'recommendation': self.recommendation
        }

        return services.get(service_name)

# 쉬운 접근을 위한 싱글톤 인스턴스
service_manager = ServiceManager()

# 개별 서비스에 쉽게 접근할 수 있는 변수들
food_db = service_manager.food_db
rag_service = service_manager.rag_service
data_processor = service_manager.data_processor
nutrition_analysis = service_manager.nutrition_analysis
food_recognition = service_manager.food_recognition
recommendation = service_manager.recommendation

def initialize_all(force_rebuild: bool = False) -> ServiceManager:
    """
    모든 서비스와 데이터베이스 초기화

    Args:
        force_rebuild: 강제로 데이터베이스 재구축 여부
    """
    service_manager.initialize_databases(force_rebuild)

    # 추가 초기화 작업이 필요한 경우 여기에 구현

    return service_manager