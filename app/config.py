import os
from datetime import timedelta
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    """기본 설정"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'nutrition-insight-secret-key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'nutrition-insight-jwt-secret')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    DEBUG = False
    TESTING = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 파일 업로드 설정
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB 이미지 업로드 제한
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'ogg'}

    # 캐시 설정
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300  # 5분

    # API 요청 제한
    RATELIMIT_DEFAULT = "200 per day, 50 per hour"
    RATELIMIT_STORAGE_URI = "memory://"

    # 외부 API 키
    FOOD_RECOGNITION_API_KEY = os.getenv('FOOD_RECOGNITION_API_KEY')
    SPEECH_TO_TEXT_API_KEY = os.getenv('SPEECH_TO_TEXT_API_KEY')
    RAG_API_KEY = os.getenv('RAG_API_KEY')

class DevelopmentConfig(Config):
    """개발 환경 설정"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URI',
                                        'sqlite:///nutrition_insight_dev.db')

class TestingConfig(Config):
    """테스트 환경 설정"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URI',
                                        'sqlite:///nutrition_insight_test.db')

class ProductionConfig(Config):
    """운영 환경 설정"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI')

    # 운영 환경 캐시 설정
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    CACHE_REDIS_PORT = os.getenv('REDIS_PORT', 6379)

    # 운영 환경 요청 제한 설정
    RATELIMIT_STORAGE_URI = os.getenv('REDIS_URI', 'redis://localhost:6379/0')

config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}