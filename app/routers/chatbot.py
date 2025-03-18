import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.responses import success_response, error_response
from services.chatbot import initialize_nutrition_chatbot

# dotenv 라이브러리 추가
from dotenv import load_dotenv

# .env 파일의 환경 변수 로드
load_dotenv()

# 환경 변수에서 OpenAI API 키 가져오기
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# 의존성 주입에 필요한 저장소/서비스 임포트
from repositories.user_repository import UserRepository
from repositories.meal_repository import MealRepository
from services.nutrition_service import NutritionService

# 챗봇 블루프린트 생성
chatbot_bp = Blueprint('chatbot', __name__)

# 챗봇 서비스 초기화
nutrition_chatbot = initialize_nutrition_chatbot(
    openai_api_key=OPENAI_API_KEY,
    user_repository=UserRepository(),
    nutrition_service=NutritionService(),
    meal_repository=MealRepository()
)

@chatbot_bp.route('/api/chat', methods=['POST'])
@jwt_required()  # JWT 인증 필요
def chat_endpoint():
    """
    개인화된 영양 챗봇 대화 엔드포인트
    """
    try:
        # 현재 인증된 사용자 ID 가져오기
        current_user_id = get_jwt_identity()

        # 요청 데이터 파싱
        data = request.get_json()
        message = data.get('message')

        # 메시지 유효성 검사
        if not message:
            return error_response('메시지를 입력해주세요.', 400)

        # 대화 의도 분석
        intent = nutrition_chatbot.analyze_conversation_intent(message)

        # 챗봇 응답 생성
        response = nutrition_chatbot.generate_chat_response(
            user_id=current_user_id,
            user_message=message
        )

        # 개인화된 추천 생성
        recommendations = nutrition_chatbot.generate_personalized_recommendation(
            user_id=current_user_id,
            intent_category=intent.get('intent_category', '기타')
        )

        # 성공 응답
        return success_response({
            'response': response.get('response', ''),
            'intent': intent,
            'recommendations': recommendations,
            'nutrition_context': response.get('nutrition_context', {})
        })

    except Exception as e:
        # 서버 오류 처리
        return error_response(f'챗봇 응답 생성 중 오류 발생: {str(e)}', 500)