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

    # 블루프린트 등록
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