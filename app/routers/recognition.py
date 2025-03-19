from flask import Blueprint, request, jsonify, current_app

recognition_bp = Blueprint('recognition', __name__)

@recognition_bp.route('/', methods=['POST'])
def recognize_food():
    """
    음식 인식 API 엔드포인트
    - 이미지 파일이 전송되면, 파일 확장자와 크기를 검증 후 음식 인식 로직 호출
    - JSON 데이터로 'text' 키가 있을 경우, 텍스트 기반 음식 인식 로직 호출
    - 둘 다 제공되지 않으면 에러 반환
    """
    try:
        # 이미지 파일 처리
        if 'image' in request.files:
            image_file = request.files['image']
            filename = image_file.filename

            # 파일 확장자 검증
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
            if '.' not in filename:
                return jsonify({"error": "파일 확장자가 없습니다."}), 400
            ext = filename.rsplit('.', 1)[1].lower()
            if ext not in allowed_extensions:
                return jsonify({"error": "지원되지 않는 이미지 형식입니다."}), 400

            # 이미지 데이터 읽기
            image_data = image_file.read()
            # 이미지 크기 제한: 10MB (예시)
            if len(image_data) > 10 * 1024 * 1024:
                return jsonify({"error": "이미지 크기가 너무 큽니다."}), 400

            # 여기서 실제 음식 인식 로직을 호출 (예: recognition_service.recognize_food_from_image(image_data))
            # 현재는 더미 데이터를 반환하도록 구현
            result = {
                "foods": ["김치찌개", "밥"],
                "confidence": 0.92
            }
            return jsonify(result)

        # 텍스트 기반 인식 처리
        elif request.is_json and 'text' in request.get_json():
            data = request.get_json()
            text = data.get('text')
            if not text or text.strip() == "":
                return jsonify({"error": "유효한 텍스트를 입력해주세요."}), 400

            # 실제 텍스트 기반 음식 인식 로직 호출 (예: recognition_service.recognize_food_from_text(text))
            # 더미 데이터 반환
            result = {
                "foods": ["김치찌개"],
                "source": "text"
            }
            return jsonify(result)
        else:
            return jsonify({"error": "이미지 파일 또는 텍스트를 제공해주세요."}), 400

    except Exception as e:
        current_app.logger.error(f"식품 인식 중 오류 발생: {str(e)}")
        return jsonify({"error": "식품 인식 중 오류가 발생했습니다."}), 500
