from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from datetime import datetime, timedelta
from app.extensions import db, jwt, limiter
from models.user import User
from utils.responses import success_response, error_response
from utils.validators import validate_email, validate_password

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
@limiter.limit("10 per hour")
def register():
    """사용자 등록 API"""
    data = request.get_json()

    # 필수 필드 체크
    for field in ['email', 'password', 'name']:
        if field not in data:
            return error_response(f'{field} 필드가 필요합니다.', 400)

    # 유효성 검사
    if not validate_email(data['email']):
        return error_response('유효하지 않은 이메일 형식입니다.', 400)

    if not validate_password(data['password']):
        return error_response('비밀번호는 최소 8자 이상이어야 하며, 문자, 숫자, 특수문자를 포함해야 합니다.', 400)

    # 이메일 중복 확인
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return error_response('이미 등록된 이메일입니다.', 409)

    # 사용자 생성
    try:
        user = User(
            email=data['email'],
            password=data['password'],
            name=data['name'],
            gender=data.get('gender'),
            birth=data.get('birth'),
            allergies=data.get('allergies'),
            health_goal=data.get('health_goal')
        )
        db.session.add(user)
        db.session.commit()

        return success_response({
            'message': '회원가입이 완료되었습니다.'
        }, 201)
    except Exception as e:
        db.session.rollback()
        return error_response(f'회원가입 처리 중 오류가 발생했습니다: {str(e)}', 500)

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("20 per hour")
def login():
    """로그인 API"""
    data = request.get_json()

    # 필수 필드 체크
    for field in ['email', 'password']:
        if field not in data:
            return error_response(f'{field} 필드가 필요합니다.', 400)

    # 사용자 검증
    user = User.query.filter_by(email=data['email']).first()
    if not user or not user.check_password(data['password']):
        return error_response('이메일 또는 비밀번호가 올바르지 않습니다.', 401)

    # 토큰 생성
    access_token = create_access_token(identity=str(user.uid))
    refresh_token = create_refresh_token(identity=str(user.uid))

    # 응답 생성
    response_data = {
        'message': '로그인 성공',
        'user': user.to_dict()
    }

    # HTTP 응답 생성
    response = make_response(jsonify(success_response(response_data)))

    # 토큰을 헤더에 추가
    response.headers['Authorization'] = f'Bearer {access_token}'
    response.headers['Refresh-Token'] = refresh_token

    return response

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """토큰 갱신 API"""
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=current_user_id)

    return success_response({
        'access_token': access_token
    })

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """로그아웃 API"""
    return success_response({
        'message': '로그아웃 성공. 클라이언트에서 토큰을 삭제해주세요.'
    })

# JWT 콜백 등록 (확장 시 사용)
@jwt.user_identity_loader
def user_identity_lookup(user_id):
    return str(user_id)

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.query.filter_by(uid=int(identity)).one_or_none()