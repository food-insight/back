import os
from dotenv import load_dotenv
from services import initialize_all, service_manager
from flask import Flask, jsonify, request
# 환경 변수 로드
load_dotenv()
# 서비스 초기화
initialize_all(force_rebuild=False)
# Flask 앱 생성
app = Flask(__name__)
# API 엔드포인트 구현
@app.route('/api/nutrition', methods=['GET'])
def get_nutrition():
    """식품 영양 정보 API"""
    food_name = request.args.get('food')
    quantity = float(request.args.get('quantity', 100))
    unit = request.args.get('unit', 'g')

    if not food_name:
        return jsonify({"error": "음식 이름을 지정해주세요."}), 400

    nutrition_service = service_manager.get_service('nutrition')
    result = nutrition_service.analyze_food_nutrients(food_name, quantity, unit)

    return jsonify(result)
@app.route('/api/recognize', methods=['POST'])
def recognize_food():
    """식품 인식 API"""
    try:
        # 이미지 파일 처리
        if 'image' in request.files:
            image_file = request.files['image']

            # 파일 확장자 및 MIME 타입 검증
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
            if not image_file.filename.lower().split('.')[-1] in allowed_extensions:
                return jsonify({"error": "지원되지 않는 이미지 형식입니다."}), 400

            # 이미지 데이터 안전하게 읽기
            image_data = image_file.read()

            # 이미지 크기 제한 (예: 10MB)
            if len(image_data) > 10 * 1024 * 1024:
                return jsonify({"error": "이미지 크기가 너무 큽니다."}), 400

            recognition_service = service_manager.get_service('recognition')
            result = recognition_service.recognize_food_from_image(image_data)

            return jsonify({
                "foods": result.get('foods', []),
                "confidence": result.get('confidence', 0)
            })

        # 텍스트 기반 인식
        elif request.json and 'text' in request.json:
            text = request.json['text']

            # 텍스트 유효성 검사
            if not text or text.strip() == '':
                return jsonify({"error": "유효한 텍스트를 입력해주세요."}), 400

            recognition_service = service_manager.get_service('recognition')
            result = recognition_service.recognize_food_from_text(text)

            return jsonify({
                "foods": result.get('foods', []),
                "source": "text"
            })

        else:
            return jsonify({"error": "이미지 파일 또는 텍스트를 제공해주세요."}), 400

    except Exception as e:
        # 예상치 못한 오류 처리
        app.logger.error(f"식품 인식 중 오류 발생: {str(e)}")
        return jsonify({"error": "식품 인식 중 오류가 발생했습니다."}), 500

@app.route('/api/recommend/similar', methods=['GET'])
def recommend_similar():
    """유사 식품 추천 API"""
    food_name = request.args.get('food')
    limit = int(request.args.get('limit', 5))

    if not food_name:
        return jsonify({"error": "음식 이름을 지정해주세요."}), 400

    recommendation_service = service_manager.get_service('recommendation')
    result = recommendation_service.get_similar_foods(food_name, limit)

    return jsonify(result)

@app.route('/api/chat', methods=['POST'])
def chatbot_conversation():
    """챗봇 대화 API"""
    data = request.json
    user_id = data.get('user_id')
    message = data.get('message')

    if not user_id or not message:
        return jsonify({"error": "사용자 ID와 메시지를 입력해주세요."}), 400

    chatbot_service = service_manager.get_service('chatbot')
    result = chatbot_service.process_conversation(user_id, message)

    return jsonify({
        "response": result.get('response', ''),
        "alternative_foods": result.get('alternative_foods', []),
        "meal_recommendations": result.get('meal_recommendations', [])
    })

@app.route('/api/recommend/meal', methods=['POST'])
def recommend_meal():
    """식단 추천 API"""
    data = request.json or {}
    preferences = data.get('preferences', [])
    restrictions = data.get('restrictions', [])

    recommendation_service = service_manager.get_service('recommendation')
    result = recommendation_service.recommend_balanced_meal(preferences, restrictions)

    return jsonify(result)
if __name__ == "__main__":
    # 개발 서버 실행
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))