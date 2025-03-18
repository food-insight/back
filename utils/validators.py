import re

def validate_email(email):
    """
    이메일 유효성 검사 함수

    Args:
        email (str): 검증할 이메일 주소

    Returns:
        bool: 유효한 이메일이면 True, 아니면 False
    """
    # 이메일 정규표현식 패턴
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    # 이메일이 None이거나 빈 문자열인 경우 False 반환
    if not email:
        return False

    # 정규표현식을 사용한 이메일 검증
    return re.match(email_regex, email) is not None

def validate_password(password):
    """
    비밀번호 유효성 검사 함수

    Args:
        password (str): 검증할 비밀번호

    Returns:
        bool: 유효한 비밀번호면 True, 아니면 False
    """
    # 비밀번호 유효성 검사 조건
    # 1. 최소 8자 이상
    # 2. 최소 1개의 대문자
    # 3. 최소 1개의 소문자
    # 4. 최소 1개의 숫자
    # 5. 최소 1개의 특수문자
    password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]).{8,}$'

    # 비밀번호가 None이거나 빈 문자열인 경우 False 반환
    if not password:
        return False

    # 정규표현식을 사용한 비밀번호 검증
    return re.match(password_regex, password) is not None