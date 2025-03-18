from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from app.extensions import db
from services.speech_to_text import transcribe_audio, extract_meal_information
from utils.responses import success_response, error_response
import os
import uuid

speech_bp = Blueprint('speech', __name__)

@speech_bp.route('/transcribe', methods=['POST'])
@jwt_required()
def transcribe_speech():
    """음성 인식 API - 일반 텍스트 변환"""
    # 오디오 파일 확인
    if 'audio' not in request.files:
        return error_response('오디오 파일이 필요합니다.', 400)

    audio_file = request.files['audio']
    if not audio_file.filename:
        return error_response('오디오 파일이 선택되지 않았습니다.', 400)

    # 파일 확장자 확인
    ext = audio_file.filename.rsplit('.', 1)[1].lower() if '.' in audio_file.filename else ''
    if ext not in current_app.config['ALLOWED_AUDIO_EXTENSIONS']:
        return error_response('허용되지 않은 파일 형식입니다.', 400)

    try:
        # 오디오 파일 저장
        filename = secure_filename(f"{uuid.uuid4()}.{ext}")
        audio_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'audio', filename)
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        audio_file.save(audio_path)

        # 음성 인식 서비스 호출
        transcript = transcribe_audio(audio_path)

        return success_response({
            'transcript': transcript
        })
    except Exception as e:
        current_app.logger.error(f"음성 인식 오류: {str(e)}")
        return error_response(f'음성 인식 실패: {str(e)}', 500)
    finally:
        # 임시 파일 삭제
        if 'audio_path' in locals() and os.path.exists(audio_path):
            os.remove(audio_path)

@speech_bp.route('/meal-record', methods=['POST'])
@jwt_required()
def record_meal_by_speech():
    """음성으로 식사 기록 API"""
    current_user_id = get_jwt_identity()

    # 오디오 파일 확인
    if 'audio' not in request.files:
        return error_response('오디오 파일이 필요합니다.', 400)

    audio_file = request.files['audio']
    if not audio_file.filename:
        return error_response('오디오 파일이 선택되지 않았습니다.', 400)

    # 파일 확장자 확인
    ext = audio_file.filename.rsplit('.', 1)[1].lower() if '.' in audio_file.filename else ''
    if ext not in current_app.config['ALLOWED_AUDIO_EXTENSIONS']:
        return error_response('허용되지 않은 파일 형식입니다.', 400)

    try:
        # 오디오 파일 저장
        filename = secure_filename(f"meal_{uuid.uuid4()}.{ext}")
        audio_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'audio', filename)
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        audio_file.save(audio_path)

        # 음성 인식 처리
        transcript = transcribe_audio(audio_path)

        # 식사 정보 추출
        meal_info = extract_meal_information(transcript)

        if not meal_info:
            return error_response('음성에서 식사 정보를 추출할 수 없습니다.', 400)

        return success_response({
            'transcript': transcript,
            'meal_info': meal_info,
            'message': '음성에서 식사 정보가 성공적으로 추출되었습니다.'
        })
    except Exception as e:
        current_app.logger.error(f"음성 식사 기록 오류: {str(e)}")
        return error_response(f'음성으로 식사 기록 실패: {str(e)}', 500)
    finally:
        # 임시 파일 삭제
        if 'audio_path' in locals() and os.path.exists(audio_path):
            os.remove(audio_path)

@speech_bp.route('/recognize-food', methods=['POST'])
@jwt_required()
def recognize_food_by_speech():
    """음성으로 음식 인식 API"""
    # 오디오 파일 확인
    if 'audio' not in request.files:
        return error_response('오디오 파일이 필요합니다.', 400)

    audio_file = request.files['audio']
    if not audio_file.filename:
        return error_response('오디오 파일이 선택되지 않았습니다.', 400)

    # 파일 확장자 확인
    ext = audio_file.filename.rsplit('.', 1)[1].lower() if '.' in audio_file.filename else ''
    if ext not in current_app.config['ALLOWED_AUDIO_EXTENSIONS']:
        return error_response('허용되지 않은 파일 형식입니다.', 400)

    try:
        # 오디오 파일 저장
        filename = secure_filename(f"food_{uuid.uuid4()}.{ext}")
        audio_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'audio', filename)
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        audio_file.save(audio_path)

        # 음성 인식 처리
        transcript = transcribe_audio(audio_path)

        # 음식 이름만 추출
        from services.food_recognition_service import extract_food_names_from_text
        food_names = extract_food_names_from_text(transcript)

        if not food_names:
            return error_response('음성에서 음식 이름을 추출할 수 없습니다.', 400)

        return success_response({
            'transcript': transcript,
            'food_names': food_names
        })
    except Exception as e:
        current_app.logger.error(f"음성 음식 인식 오류: {str(e)}")
        return error_response(f'음성으로 음식 인식 실패: {str(e)}', 500)
    finally:
        # 임시 파일 삭제
        if 'audio_path' in locals() and os.path.exists(audio_path):
            os.remove(audio_path)