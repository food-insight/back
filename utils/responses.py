from flask import jsonify

def success_response(data=None, message="Success", status_code=200):
    """
    성공 응답을 생성하는 표준 함수
    
    :param data: 응답과 함께 보낼 데이터 (선택적)
    :param message: 성공 메시지 (기본값: "Success")
    :param status_code: HTTP 상태 코드 (기본값: 200)
    :return: Flask JSON 응답
    """
    response = {
        "success": True,
        "message": message
    }

    if data is not None:
        response["data"] = data

    return jsonify(response), status_code

def error_response(message="Error", status_code=400, details=None):
    """
    오류 응답을 생성하는 표준 함수
    
    :param message: 오류 메시지 (기본값: "Error")
    :param status_code: HTTP 상태 코드 (기본값: 400)
    :param details: 추가 오류 상세 정보 (선택적)
    :return: Flask JSON 응답
    """
    response = {
        "success": False,
        "message": message
    }

    if details is not None:
        response["details"] = details

    return jsonify(response), status_code