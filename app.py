import os
from dotenv import load_dotenv
from services import initialize_all

# 환경 변수 로드
load_dotenv()

# 모델 임포트 - 이 부분이 중요합니다!
import models

# 서비스 초기화
initialize_all(force_rebuild=False)

# 앱 팩토리 함수 가져오기
from app import create_app

# 앱 생성
app = create_app(config_name='development')

# 직접 실행할 경우
if __name__ == "__main__":
    # 개발 서버 실행
    port = int(os.getenv('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)