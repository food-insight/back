from app.extensions import db
from flask import current_app
import logging

logger = logging.getLogger(__name__)

def init_database():
    """데이터베이스 초기화"""
    try:
        logger.info("데이터베이스 초기화 시작")

        # 테이블 생성
        db.create_all()
        logger.info("데이터베이스 테이블 생성 완료")

        # 시드 데이터 추가 여부 확인
        if current_app.config.get('SEED_DB', False):
            logger.info("시드 데이터 생성 중...")
            from database.seeds import seed_all
            seed_all()
            logger.info("시드 데이터 생성 완료")

        return True
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {str(e)}")
        return False

def reset_database():
    """데이터베이스 초기화 (기존 데이터 삭제)"""
    try:
        logger.info("데이터베이스 리셋 시작")

        # 테이블 삭제 후 재생성
        db.drop_all()
        logger.info("데이터베이스 테이블 삭제 완료")

        db.create_all()
        logger.info("데이터베이스 테이블 재생성 완료")

        # 시드 데이터 추가 여부 확인
        if current_app.config.get('SEED_DB', False):
            logger.info("시드 데이터 생성 중...")
            from database.seeds import seed_all
            seed_all()
            logger.info("시드 데이터 생성 완료")

        return True
    except Exception as e:
        logger.error(f"데이터베이스 리셋 실패: {str(e)}")
        return False

if __name__ == "__main__":
    from app import create_app

    app = create_app()
    with app.app_context():
        # 명령줄에서 실행할 경우 데이터베이스 초기화
        reset = input("데이터베이스를 리셋하시겠습니까? (y/n): ").lower() == 'y'

        if reset:
            result = reset_database()
        else:
            result = init_database()

        if result:
            print("데이터베이스 초기화/리셋이 성공적으로 완료되었습니다.")
        else:
            print("데이터베이스 초기화/리셋 중 오류가 발생했습니다.")