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
    if 'image' in request.files:
        # 이미지 인식
        image_file = request.files['image']
        image_data = image_file.read()

        recognition_service = service_manager.get_service('recognition')
        result = recognition_service.recognize_food_from_image(image_data)

        return jsonify(result)
    elif request.json and 'text' in request.json:
        # 텍스트 기반 인식
        text = request.json['text']

        recognition_service = service_manager.get_service('recognition')
        result = recognition_service.recognize_food_from_text(text)

        return jsonify(result)
    else:
        return jsonify({"error": "이미지 파일 또는 텍스트를 제공해주세요."}), 400
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
@app.route('/api/recommend/meal', methods=['POST'])
def recommend_meal():
    """식단 추천 API"""
    data = request.json or {}
    preferences = data.get('preferences', [])
    restrictions = data.get('restrictions', [])

    recommendation_service = service_manager.get_service('recommendation')
    result = recommendation_service.recommend_balanced_meal(preferences, restrictions)

    return jsonify(result)
if __name__ == "main":
    # 개발 서버 실행
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))