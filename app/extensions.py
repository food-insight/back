from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache

# 데이터베이스
db = SQLAlchemy()

# 마이그레이션
migrate = Migrate()

# JWT
jwt = JWTManager()

# API 요청 제한
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# 캐시
cache = Cache()