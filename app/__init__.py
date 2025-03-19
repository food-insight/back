from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from app.config import config_by_name
from app.extensions import db, migrate, jwt, limiter, cache

def create_app(config_name='development'):
    """애플리케이션 팩토리 함수"""
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # 확장 프로그램 초기화
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)
    CORS(app)

    # 블루프린트 등록 - 지연 임포트 사용
    with app.app_context():
        # 여기에서 블루프린트를 가져오면 앱 컨텍스트 내에서 가져오므로 순환 참조 방지
        from app.routers.auth import auth_bp
        from app.routers.meal import meal_bp
        from app.routers.nutrition import nutrition_bp
        from app.routers.recommendation import recommendation_bp
        from app.routers.user import user_bp
        from app.routers.chatbot import chatbot_bp
        from app.routers.image import image_bp
        from app.routers.speech import speech_bp
        from app.routers.main import main_bp

        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.register_blueprint(meal_bp, url_prefix='/api/meals')
        app.register_blueprint(nutrition_bp, url_prefix='/api/nutrition')
        app.register_blueprint(recommendation_bp, url_prefix='/api/recommendations')
        app.register_blueprint(user_bp, url_prefix='/api/users')
        app.register_blueprint(chatbot_bp, url_prefix='/api/chatbot')
        app.register_blueprint(image_bp, url_prefix='/api/images')
        app.register_blueprint(speech_bp, url_prefix='/api/speech')
        app.register_blueprint(main_bp, url_prefix='/api/main')

    # 오류 핸들러 등록
    register_error_handlers(app)

    # API 엔드포인트 추가
    register_api_endpoints(app)

    return app

def register_error_handlers(app):
    """오류 핸들러 등록"""
    @app.errorhandler(404)
    def handle_not_found(e):
        return {'error': 'Not found'}, 404

    @app.errorhandler(400)
    def handle_bad_request(e):
        return {'error': 'Bad request'}, 400

    @app.errorhandler(401)
    def handle_unauthorized(e):
        return {'error': 'Unauthorized'}, 401

    @app.errorhandler(403)
    def handle_forbidden(e):
        return {'error': 'Forbidden'}, 403

    @app.errorhandler(500)
    def handle_server_error(e):
        return {'error': 'Internal server error'}, 500

def register_api_endpoints(app):
    """API 엔드포인트 등록"""
    from flask import jsonify, request
    from services import service_manager

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