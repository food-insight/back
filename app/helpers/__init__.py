import os
from app import create_app
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경 변수에서 설정 가져오기 (기본값: development)
config_name = os.getenv('FLASK_CONFIG', 'development')

# 애플리케이션 생성
app = create_app(config_name)

if __name__ == '__main__':
    # 애플리케이션 실행
    app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=(config_name == 'development')
    )