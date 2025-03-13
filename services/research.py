import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# AI 모델 관련 라이브러리
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

class NutritionResearchService:
    """
    최신 영양학 연구 및 건강 트렌드 추적 서비스
    """
    def __init__(
            self,
            openai_api_key: str,
            research_repository=None,
            context_window_days: int = 30
    ):
        """
        연구 서비스 초기화

        Args:
            openai_api_key (str): OpenAI API 키
            research_repository: 연구 데이터 저장소 (선택적)
            context_window_days (int): 트렌드 분석 기간
        """
        self.logger = logging.getLogger(__name__)

        # AI 모델 초기화
        self.llm = ChatOpenAI(
            openai_api_key=openai_api_key,
            model_name="gpt-3.5-turbo",
            temperature=0.3
        )

        # 저장소 및 설정
        self.research_repository = research_repository
        self.context_window_days = context_window_days

    def fetch_latest_nutrition_research(
            self,
            topic: str,
            limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        특정 주제의 최신 영양학 연구 정보 수집

        Args:
            topic (str): 연구 주제
            limit (int): 조회할 최대 연구 수

        Returns:
            List[Dict[str, Any]]: 연구 정보 목록
        """
        try:
            # 연구 저장소가 있는 경우 저장소에서 조회
            if self.research_repository:
                research_list = self.research_repository.get_latest_research(
                    topic,
                    limit=limit,
                    days=self.context_window_days
                )
                return research_list

            # 저장소 없을 경우 LLM 기반 연구 시뮬레이션
            research_prompt = PromptTemplate(
                input_variables=["topic"],
                template="""
                다음 주제에 대한 가장 최근의 과학적 연구 {limit}개를 요약해주세요:
                주제: {topic}

                각 연구에 대해 다음 형식으로 제공하세요:
                1. 제목
                2. 주요 발견점
                3. 실무적 시사점
                4. 연구 연도
                """
            )

            # LLM 체인 생성
            research_chain = LLMChain(llm=self.llm, prompt=research_prompt)

            # 연구 정보 생성
            research_result = research_chain.run(topic=topic, limit=limit)

            # 연구 결과 파싱 (실제로는 더 정교한 파싱 필요)
            research_list = [
                {
                    "title": line.split('.')[0],
                    "year": datetime.now().year
                }
                for line in research_result.split('\n')
                if line.strip() and '.' in line
            ]

            return research_list

        except Exception as e:
            self.logger.error(f"연구 정보 수집 중 오류: {str(e)}")
            return []

    def analyze_nutrition_trends(
            self,
            health_goal: Optional[str] = None,
            age_group: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        영양 트렌드 심층 분석

        Args:
            health_goal (Optional[str]): 건강 목표
            age_group (Optional[str]): 연령대

        Returns:
            Dict[str, Any]: 트렌드 분석 결과
        """
        try:
            # 트렌드 분석 프롬프트
            trend_prompt = PromptTemplate(
                input_variables=["health_goal", "age_group"],
                template="""
                다음 조건에 맞는 최신 영양 트렌드를 분석해주세요:
                건강 목표: {health_goal}
                연령대: {age_group}

                분석 내용:
                1. 주요 영양 트렌드
                2. 과학적 근거
                3. 실천 가능한 권장사항
                4. 주목할 만한 연구 동향
                """
            )

            # LLM 체인 생성
            trend_chain = LLMChain(llm=self.llm, prompt=trend_prompt)

            # 트렌드 분석 실행
            trend_result = trend_chain.run(
                health_goal=health_goal or "전체",
                age_group=age_group or "성인"
            )

            return {
                "trend_analysis": trend_result,
                "health_goal": health_goal,
                "age_group": age_group,
                "last_updated": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"트렌드 분석 중 오류: {str(e)}")
            return {}

    def generate_personalized_nutrition_insights(
            self,
            user: Any
    ) -> Dict[str, Any]:
        """
        사용자 맞춤형 영양 인사이트 생성

        Args:
            user (Any): 사용자 정보

        Returns:
            Dict[str, Any]: 개인화된 영양 인사이트
        """
        try:
            # 사용자 건강 목표 및 연령대 기반 트렌드 분석
            trend_analysis = self.analyze_nutrition_trends(
                health_goal=user.health_goal,
                age_group=self._get_age_group(user.age)
            )

            # 최신 연구 조회
            latest_research = self.fetch_latest_nutrition_research(
                topic=user.health_goal or "영양"
            )

            # 개인화된 인사이트 생성
            personalized_insights = {
                "user_profile": {
                    "health_goal": user.health_goal,
                    "age_group": self._get_age_group(user.age)
                },
                "nutrition_trends": trend_analysis,
                "latest_research": latest_research,
                "personalized_recommendations": self._generate_personalized_recommendations(user)
            }

            return personalized_insights

        except Exception as e:
            self.logger.error(f"개인화된 영양 인사이트 생성 중 오류: {str(e)}")
            return {}

    def _get_age_group(self, age: int) -> str:
        """
        나이를 연령대로 변환

        Args:
            age (int): 사용자 나이

        Returns:
            str: 연령대 문자열
        """
        if age < 13:
            return "아동"
        elif 13 <= age < 20:
            return "청소년"
        elif 20 <= age < 40:
            return "청년"
        elif 40 <= age < 60:
            return "중년"
        else:
            return "노년"

    def _generate_personalized_recommendations(self, user: Any) -> List[Dict[str, str]]:
        """
        개인화된 영양 추천 생성

        Args:
            user (Any): 사용자 정보

        Returns:
            List[Dict[str, str]]: 개인화된 영양 추천 목록
        """
        personalized_recommendations = {
            "체중 감량": [
                {
                    "title": "식단 최적화",
                    "description": "저칼로리 고단백 식품으로 포만감 유지"
                },
                {
                    "title": "대사 촉진",
                    "description": "규칙적인 운동과 소식 빈도로 대사율 향상"
                }
            ],
            "근육 증가": [
                {
                    "title": "단백질 섭취 전략",
                    "description": "체중 1kg당 1.6-2.2g의 양질의 단백질 섭취"
                },
                {
                    "title": "영양 타이밍",
                    "description": "운동 전후 적절한 단백질 및 탄수화물 섭취"
                }
            ],
            "당뇨 관리": [
                {
                    "title": "혈당 조절",
                    "description": "저당지수 식품 선택 및 규칙적인 식사"
                },
                {
                    "title": "영양소 균형",
                    "description": "복합 탄수화물, 식이섬유, 건강한 지방 섭취"
                }
            ],
            "일반 건강": [
                {
                    "title": "균형 잡힌 식단",
                    "description": "다양한 영양소를 고루 섭취"
                },
                {
                    "title": "수분 섭취",
                    "description": "하루 8잔 이상의 물 섭취"
                }
            ]
        }

        # 건강 목표에 따른 맞춤 추천, 기본값은 일반 건강
        return personalized_recommendations.get(
            user.health_goal,
            personalized_recommendations["일반 건강"]
        )

def initialize_research_service(
        openai_api_key: str,
        research_repository=None
) -> NutritionResearchService:
    """
    연구 서비스 초기화

    Args:
        openai_api_key (str): OpenAI API 키
        research_repository: 연구 데이터 저장소 (선택적)

    Returns:
        NutritionResearchService: 초기화된 연구 서비스
    """
    return NutritionResearchService(
        openai_api_key=openai_api_key,
        research_repository=research_repository
    )