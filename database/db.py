from app.extensions import db
from flask import current_app
import logging

logger = logging.getLogger(__name__)

def init_db():
    """데이터베이스 초기화"""
    try:
        db.create_all()
        logger.info("데이터베이스가 성공적으로 초기화되었습니다.")
    except Exception as e:
        logger.error(f"데이터베이스 초기화 오류: {str(e)}")
        raise

def drop_db():
    """데이터베이스 삭제"""
    try:
        db.drop_all()
        logger.info("데이터베이스가 성공적으로 삭제되었습니다.")
    except Exception as e:
        logger.error(f"데이터베이스 삭제 오류: {str(e)}")
        raise

def commit():
    """변경사항 커밋"""
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"트랜잭션 커밋 오류: {str(e)}")
        raise

def add(obj):
    """객체 추가"""
    try:
        db.session.add(obj)
    except Exception as e:
        logger.error(f"객체 추가 오류: {str(e)}")
        raise

def add_all(objs):
    """여러 객체 추가"""
    try:
        db.session.add_all(objs)
    except Exception as e:
        logger.error(f"여러 객체 추가 오류: {str(e)}")
        raise

def delete(obj):
    """객체 삭제"""
    try:
        db.session.delete(obj)
    except Exception as e:
        logger.error(f"객체 삭제 오류: {str(e)}")
        raise

def rollback():
    """변경사항 롤백"""
    try:
        db.session.rollback()
        logger.info("트랜잭션이 롤백되었습니다.")
    except Exception as e:
        logger.error(f"트랜잭션 롤백 오류: {str(e)}")
        raise

def execute_raw_sql(sql, params=None):
    """Raw SQL 실행"""
    try:
        if params:
            result = db.session.execute(sql, params)
        else:
            result = db.session.execute(sql)
        return result
    except Exception as e:
        db.session.rollback()
        logger.error(f"SQL 실행 오류: {str(e)}")
        raise