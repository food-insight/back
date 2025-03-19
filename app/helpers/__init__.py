# 이 파일은 순환 참조를 방지하기 위해 app을 여기서 생성하지 않습니다
# 기존의 app = create_app(config_name) 코드를 제거합니다

# 유틸리티 함수나 필요한 공통 요소만 정의합니다
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 기타 필요한 헬퍼 함수들
def format_response(data, message=None, success=True):
    """API 응답 형식화"""
    response = {
        "success": success,
        "data": data
    }
    if message:
        response["message"] = message
    return response