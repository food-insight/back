from typing import Dict, Any
from services.chatbot import PersonalizedNutritionChatbot, initialize_nutrition_chatbot

class ChatbotService:
    def __init__(self, chatbot: PersonalizedNutritionChatbot):
        """
        챗봇 서비스 초기화

        Args:
            chatbot (PersonalizedNutritionChatbot): 초기화된 챗봇 객체
        """
        self.chatbot = chatbot

    def process_conversation(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        대화 처리 메서드

        Args:
            user_id (str): 사용자 ID
            message (str): 사용자 메시지

        Returns:
            Dict[str, Any]: 챗봇 응답
        """
        # 대화 의도 분석
        intent = self.chatbot.analyze_conversation_intent(message)

        # 챗봇 응답 생성
        response = self.chatbot.generate_chat_response(
            user_id=user_id,
            user_message=message
        )

        # 개인화된 추천 생성
        recommendations = self.chatbot.generate_personalized_recommendation(
            user_id=user_id,
            intent_category=intent.get('intent_category', '기타')
        )

        return {
            'response': response.get('response', ''),
            'alternative_foods': recommendations.get('recent_foods', []),
            'meal_recommendations': recommendations.get('suggested_actions', []),
            'intent': intent
        }