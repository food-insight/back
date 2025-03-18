# app/utils/response.py
def success_response(data, status_code=200):
    """성공 응답 반환"""
    if isinstance(data, dict):
        return data
    return {"data": data, "status_code": status_code}

def error_response(message, status_code=400):
    """오류 응답 반환"""
    return {"detail": message, "status_code": status_code}