from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from models.user import User
from models.allergy import Allergy
from utils.responses import success_response, error_response
from utils.validators import validate_email, validate_password
from datetime import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """사용자 프로필 조회 API"""
    current_user_id = get_jwt_identity()

    user = User.query.filter_by(uid=current_user_id).first()
    if not user:
        return error_response('사용자를 찾을 수 없습니다.', 404)

    # 알레르기 정보 조회
    allergies = Allergy.query.filter_by(uid=current_user_id).all()
    allergy_list = [allergy.to_dict() for allergy in allergies]

    user_data = user.to_dict()
    user_data['allergies_detail'] = allergy_list

    return success_response({
        'user': user_data
    })

@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """사용자 프로필 업데이트 API"""
    current_user_id = get_jwt_identity()

    user = User.query.filter_by(uid=current_user_id).first()
    if not user:
        return error_response('사용자를 찾을 수 없습니다.', 404)

    data = request.get_json()

    try:
        # 이메일 업데이트
        if 'email' in data:
            if not validate_email(data['email']):
                return error_response('유효하지 않은 이메일 형식입니다.', 400)

            # 이메일 중복 확인
            if data['email'] != user.email:
                existing_user = User.query.filter_by(email=data['email']).first()
                if existing_user:
                    return error_response('이미 사용 중인 이메일입니다.', 409)

            user.email = data['email']

        # 비밀번호 업데이트
        if 'password' in data:
            if not validate_password(data['password']):
                return error_response('비밀번호는 최소 8자 이상이어야 하며, 문자, 숫자, 특수문자를 포함해야 합니다.', 400)

            user.password = data['password']

        # 기본 정보 업데이트
        if 'name' in data:
            user.name = data['name']

        if 'gender' in data:
            user.gender = data['gender']

        if 'birth' in data:
            try:
                user.birth = datetime.strptime(data['birth'], '%Y-%m-%d').date()
            except ValueError:
                return error_response('생년월일 형식이 올바르지 않습니다. YYYY-MM-DD 형식이어야 합니다.', 400)

        if 'health_goal' in data:
            user.health_goal = data['health_goal']

        # 알레르기 정보 업데이트
        if 'allergies' in data:
            # 기존 알레르기 정보 삭제
            Allergy.query.filter_by(uid=current_user_id).delete()

            # 새 알레르기 정보 추가
            if isinstance(data['allergies'], list):
                for allergy_name in data['allergies']:
                    allergy = Allergy(uid=current_user_id, allergy_name=allergy_name)
                    db.session.add(allergy)

        db.session.commit()

        return success_response({
            'message': '프로필이 성공적으로 업데이트되었습니다.',
            'user': user.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"프로필 업데이트 오류: {str(e)}")
        return error_response(f'프로필 업데이트 실패: {str(e)}', 500)

@user_bp.route('/allergies', methods=['GET'])
@jwt_required()
def get_allergies():
    """사용자 알레르기 정보 조회 API"""
    current_user_id = get_jwt_identity()

    allergies = Allergy.query.filter_by(uid=current_user_id).all()

    return success_response({
        'allergies': [allergy.to_dict() for allergy in allergies]
    })

@user_bp.route('/allergies', methods=['POST'])
@jwt_required()
def add_allergy():
    """알레르기 정보 추가 API"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if 'allergy_name' not in data:
        return error_response('allergy_name 필드가 필요합니다.', 400)

    allergy_name = data['allergy_name']

    # 중복 확인
    existing_allergy = Allergy.query.filter_by(
        uid=current_user_id,
        allergy_name=allergy_name
    ).first()

    if existing_allergy:
        return error_response('이미 등록된 알레르기입니다.', 409)

    try:
        allergy = Allergy(
            uid=current_user_id,
            allergy_name=allergy_name,
            fid=data.get('fid')  # 특정 음식과 연결 (선택)
        )
        db.session.add(allergy)
        db.session.commit()

        return success_response({
            'message': '알레르기 정보가 추가되었습니다.',
            'allergy': allergy.to_dict()
        }, 201)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"알레르기 추가 오류: {str(e)}")
        return error_response(f'알레르기 정보 추가 실패: {str(e)}', 500)

@user_bp.route('/allergies/<int:allergy_id>', methods=['DELETE'])
@jwt_required()
def delete_allergy(allergy_id):
    """알레르기 정보 삭제 API"""
    current_user_id = get_jwt_identity()

    allergy = Allergy.query.filter_by(aid=allergy_id, uid=current_user_id).first()
    if not allergy:
        return error_response('알레르기 정보를 찾을 수 없습니다.', 404)

    try:
        db.session.delete(allergy)
        db.session.commit()

        return success_response({
            'message': '알레르기 정보가 삭제되었습니다.'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"알레르기 삭제 오류: {str(e)}")
        return error_response(f'알레르기 정보 삭제 실패: {str(e)}', 500)

@user_bp.route('/health-goal', methods=['PUT'])
@jwt_required()
def update_health_goal():
    """건강 목표 업데이트 API"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if 'health_goal' not in data:
        return error_response('health_goal 필드가 필요합니다.', 400)

    user = User.query.filter_by(uid=current_user_id).first()
    if not user:
        return error_response('사용자를 찾을 수 없습니다.', 404)

    try:
        user.health_goal = data['health_goal']
        db.session.commit()

        return success_response({
            'message': '건강 목표가 업데이트되었습니다.',
            'health_goal': user.health_goal
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"건강 목표 업데이트 오류: {str(e)}")
        return error_response(f'건강 목표 업데이트 실패: {str(e)}', 500)

@user_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_user_dashboard():
    """사용자 대시보드 정보 API"""
    current_user_id = get_jwt_identity()

    user = User.query.filter_by(uid=current_user_id).first()
    if not user:
        return error_response('사용자를 찾을 수 없습니다.', 404)

    # 최근 식사 기록 (최대 5개)
    from models.meal import Meal
    recent_meals = Meal.query.filter_by(uid=current_user_id) \
        .order_by(Meal.date.desc(), Meal.mid.desc()) \
        .limit(5) \
        .all()

    # 알레르기 정보
    allergies = Allergy.query.filter_by(uid=current_user_id).all()

    # 최근 추천 정보 (최대 3개)
    from models.recommendation import Recommendation
    recent_recommendations = Recommendation.query.filter_by(uid=current_user_id) \
        .order_by(Recommendation.rid.desc()) \
        .limit(3) \
        .all()

    return success_response({
        'user': user.to_dict(),
        'recent_meals': [meal.to_dict() for meal in recent_meals],
        'allergies': [allergy.to_dict() for allergy in allergies],
        'recent_recommendations': [rec.to_dict() for rec in recent_recommendations],
        'health_goal': user.health_goal
    })