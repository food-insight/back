from app import create_app
from app.extensions import db
from models.user import User
from models.allergy import Allergy

def migrate_allergies():
    """
    기존 사용자의 알레르기 정보를 User.allergies 필드에서 Allergy 테이블로 마이그레이션하는 스크립트
    """
    app = create_app('development')
    with app.app_context():
        # 모든 사용자 조회
        users = User.query.all()
        print(f"총 {len(users)}명의 사용자 정보를 확인합니다.")

        migrated_count = 0
        for user in users:
            # User.allergies 필드에서 알레르기 정보 가져오기
            allergies_str = user.allergies or ""
            if allergies_str:
                allergies_list = allergies_str.split(",")
                print(f"사용자 ID {user.uid}, 이메일 {user.email}: {len(allergies_list)}개의 알레르기 정보 처리 중")

                # 각 알레르기를 Allergy 테이블에 추가
                for allergy_name in allergies_list:
                    if allergy_name.strip():
                        # 중복 확인
                        existing = Allergy.query.filter_by(uid=user.uid, allergy_name=allergy_name.strip()).first()
                        if not existing:
                            print(f"   - 알레르기 추가: {allergy_name.strip()}")
                            allergy = Allergy(uid=user.uid, allergy_name=allergy_name.strip())
                            db.session.add(allergy)
                            migrated_count += 1
                        else:
                            print(f"   - 이미 존재하는 알레르기: {allergy_name.strip()}")

        # 변경사항 저장
        if migrated_count > 0:
            db.session.commit()
            print(f"알레르기 정보 마이그레이션 완료: {migrated_count}개의 알레르기 정보 추가됨")
        else:
            print("마이그레이션할 알레르기 정보가 없습니다.")

if __name__ == "__main__":
    migrate_allergies()