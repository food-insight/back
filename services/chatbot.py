import logging
from typing import List, Dict, Any, Optional
import json
from datetime import datetime, timedelta
import os

# AI 모델 관련 라이브러리
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# 의존성 주입용 추상 클래스
from abc import ABC, abstractmethod

class UserRepository(ABC):
    @abstractmethod
    def get_user(self, user_id: str):
        pass

class NutritionService(ABC):
    @abstractmethod
    def calculate_daily_nutrition(self, meals):
        pass

    @abstractmethod
    def get_nutrition_insights(self, daily_nutrition, is_average=True):
        pass

    @abstractmethod
    def get_recipe_recommendations(self, health_goal: str):
        pass

    @abstractmethod
    def get_food_nutrition(self, food_name: str):
        pass

class MealRepository(ABC):
    @abstractmethod
    def get_meals_by_date_range(self, user_id, start_date, end_date):
        pass

    @abstractmethod
    def get_recent_meals(self, user_id, limit=3):
        pass

class PersonalizedNutritionChatbot:
    """
    개인화된 영양 상담 챗봇 서비스
    """
    def __init__(
            self,
            openai_api_key: str,
            user_repository: UserRepository,
            nutrition_service: NutritionService,
            meal_repository: MealRepository,
            context_window_days: int = 7
    ):
        """
        챗봇 서비스 초기화
        """
        self.logger = logging.getLogger(__name__)

        # AI 모델 초기화
        self.llm = ChatOpenAI(
            openai_api_key=openai_api_key,
            model_name="gpt-3.5-turbo",
            temperature=0.5
        )

        # 서비스 및 저장소 의존성 주입
        self.user_repository = user_repository
        self.nutrition_service = nutrition_service
        self.meal_repository = meal_repository
        self.context_window_days = context_window_days

        # 대화 프롬프트 템플릿 설정
        self._setup_conversation_template()

    def _setup_conversation_template(self):
        """
        대화 프롬프트 템플릿 설정
        """
        self.conversation_prompt = PromptTemplate(
            input_variables=[
                "user_profile",
                "recent_nutrition",
                "health_goal",
                "conversation_history",
                "user_message"
            ],
            template="""
            너는 개인화된 영양 상담 AI 어시스턴트야.

            사용자 프로필:
            {user_profile}

            최근 영양 섭취 현황:
            {recent_nutrition}

            건강 목표: {health_goal}

            대화 이력:
            {conversation_history}

            사용자 메시지: {user_message}

            전문적이고 친절한 맞춤형 영양 조언을 제공해. 
            사용자의 건강 목표와 최근 영양 섭취 상태를 고려해서 구체적이고 실천 가능한 조언을 해.
            """
        )

    def _get_recent_nutrition_context(self, user_id: str) -> Dict[str, Any]:
        """
        최근 영양 섭취 컨텍스트 조회
        """
        try:
            # 최근 식사 기록 조회 (지정된 기간 내)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.context_window_days)

            recent_meals = self.meal_repository.get_meals_by_date_range(
                user_id, start_date, end_date
            )

            # 영양 분석
            daily_nutrition = self.nutrition_service.calculate_daily_nutrition(recent_meals)
            nutrition_insights = self.nutrition_service.get_nutrition_insights(
                daily_nutrition,
                is_average=True
            )

            return {
                "daily_nutrition": daily_nutrition,
                "nutrition_insights": nutrition_insights
            }

        except Exception as e:
            self.logger.error(f"최근 영양 컨텍스트 조회 중 오류: {str(e)}")
            return {}

    def generate_chat_response(
            self,
            user_id: str,
            user_message: str,
            conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        개인화된 챗봇 응답 생성
        """
        try:
            # 사용자 정보 조회
            user = self.user_repository.get_user(user_id)

            # 최근 영양 컨텍스트 조회
            nutrition_context = self._get_recent_nutrition_context(user_id)

            # 대화 이력 처리
            conversation_history = conversation_history or []
            history_str = "\n".join([
                f"사용자: {entry['user']}\n어시스턴트: {entry['assistant']}"
                for entry in conversation_history[-5:]  # 최근 5개 대화만 포함
            ])

            # LLM 체인 생성
            chain = LLMChain(llm=self.llm, prompt=self.conversation_prompt)

            # 응답 생성
            response = chain.run(
                user_profile=json.dumps(user.__dict__, ensure_ascii=False),
                recent_nutrition=json.dumps(nutrition_context, ensure_ascii=False),
                health_goal=user.health_goal,
                conversation_history=history_str,
                user_message=user_message
            )

            return {
                "response": response,
                "nutrition_context": nutrition_context
            }

        except Exception as e:
            self.logger.error(f"챗봇 응답 생성 중 오류: {str(e)}")
            return {
                "response": "죄송합니다. 현재 상담이 어렵습니다. 잠시 후 다시 시도해주세요.",
                "nutrition_context": {}
            }

    def analyze_conversation_intent(self, user_message: str) -> Dict[str, Any]:
        """
        사용자 메시지의 의도 분석
        """
        try:
            # 대화 의도 분석을 위한 프롬프트
            intent_prompt = PromptTemplate(
                input_variables=["user_message"],
                template="""
                다음 메시지의 주요 의도를 분석해줘. 
                가능한 의도 카테고리:
                - 영양 상담 (건강 조언, 식단 평가)
                - 식품 정보 (특정 음식의 영양 정보)
                - 건강 목표 관련 (체중 관리, 근육 증가 등)
                - 레시피 추천
                - 일반 대화
                - 기타

                메시지: {user_message}

                의도 분석 결과를 다음 JSON 형식으로 제공해:
                {{
                    "intent_category": "...",
                    "confidence": 0.0,
                    "key_entities": []
                }}
                """
            )

            # LLM 체인 생성
            intent_chain = LLMChain(llm=self.llm, prompt=intent_prompt)

            # 의도 분석 실행
            intent_result_str = intent_chain.run(user_message=user_message)

            # JSON 파싱 (안전한 파싱)
            try:
                intent_result = json.loads(intent_result_str)
            except json.JSONDecodeError:
                # 파싱 실패 시 기본값
                intent_result = {
                    "intent_category": "기타",
                    "confidence": 0.5,
                    "key_entities": []
                }

            return intent_result

        except Exception as e:
            self.logger.error(f"대화 의도 분석 중 오류: {str(e)}")
            return {
                "intent_category": "기타",
                "confidence": 0.5,
                "key_entities": []
            }

    def generate_personalized_recommendation(
            self,
            user_id: str,
            intent_category: str
    ) -> Dict[str, Any]:
        """
        의도에 기반한 개인화된 추천 생성
        """
        try:
            # 사용자 정보 조회
            user = self.user_repository.get_user(user_id)

            # 의도별 추천 로직
            recommendations = {}

            if intent_category == "레시피 추천":
                # 레시피 추천 (건강 목표 기반)
                recommendations = self.nutrition_service.get_recipe_recommendations(
                    health_goal=user.health_goal
                )

            elif intent_category == "식품 정보":
                # 최근 많이 섭취한 음식 기반 정보 제공
                recent_meals = self.meal_repository.get_recent_meals(user_id, limit=3)
                recommendations = {
                    "recent_foods": [
                        self.nutrition_service.get_food_nutrition(meal.food_name)
                        for meal in recent_meals
                    ]
                }

            elif intent_category == "건강 목표 관련":
                # 건강 목표 진행 상황 및 추천
                nutrition_context = self._get_recent_nutrition_context(user_id)
                recommendations = {
                    "health_goal": user.health_goal,
                    "nutrition_progress": nutrition_context,
                    "suggested_actions": self._generate_goal_specific_recommendations(user)
                }

            else:
                # 기본 영양 추천
                recommendations = {
                    "general_nutrition_tips": self._generate_general_nutrition_tips(user)
                }

            return recommendations

        except Exception as e:
            self.logger.error(f"개인화된 추천 생성 중 오류: {str(e)}")
            return {}

    def _generate_goal_specific_recommendations(self, user):
        """
        건강 목표별 맞춤 추천 생성
        """
        goal_recommendations = {
            "체중 감량": [
                {
                    "title": "식단 조절",
                    "description": "저칼로리, 고단백 식품 섭취로 포만감 유지"
                },
                {
                    "title": "운동 병행",
                    "description": "유산소 운동과 근력 운동 균형 있게 진행"
                }
            ],
            "근육 증가": [
                {
                    "title": "단백질 섭취",
                    "description": "매 끼니 양질의 단백질 섭취, 체중 1kg당 1.6-2.2g"
                },
                {
                    "title": "운동 타이밍",
                    "description": "운동 전후 적절한 단백질 섭취로 근육 성장 촉진"
                }
            ],
            "당뇨 관리": [
                {
                    "title": "탄수화물 관리",
                    "description": "저당지수 식품 선택, 탄수화물 섭취 조절"
                },
                {
                    "title": "식사 규칙성",
                    "description": "규칙적인 식사와 소식 빈도로 혈당 안정화"
                }
            ]
        }

        return goal_recommendations.get(
            user.health_goal,
            [{"title": "건강한 식습관", "description": "균형 잡힌 영양 섭취"}]
        )

    def _generate_general_nutrition_tips(self, user):
        """
        일반적인 영양 팁 생성
        """
        return [
            {
                "title": "균형 잡힌 식단",
                "description": "다양한 영양소를 고루 섭취하세요."
            },
            {
                "title": "수분 섭취",
                "description": "하루 8잔 이상의 물을 마시세요."
            },
            {
                "title": "규칙적인 식사",
                "description": "하루 세 끼 규칙적으로 섭취하세요."
            }
        ]

def initialize_nutrition_chatbot(
        openai_api_key: str,
        user_repository: UserRepository,
        nutrition_service: NutritionService,
        meal_repository: MealRepository
) -> PersonalizedNutritionChatbot:
    """
    영양 챗봇 서비스 초기화
    """
    return PersonalizedNutritionChatbot(
        openai_api_key=openai_api_key,
        user_repository=user_repository,
        nutrition_service=nutrition_service,
        meal_repository=meal_repository
    )