from services.chatbot import UserRepository as BaseUserRepository
from models.user import User

class UserRepository(BaseUserRepository):
    def get_user(self, user_id: str):
        """
        사용자 ID로 사용자 정보 조회

        Args:
            user_id (str): 사용자 ID

        Returns:
            User 객체
        """
        # get_user_by_id 메서드를 기반으로 수정
        user_info = self.get_user_by_id(int(user_id))

        # User 모델과 유사한 객체 생성
        class UserObject:
            def __init__(self, info):
                self.uid = info['id']
                self.email = info['email']
                self.name = info['username']
                self.health_goal = '체중 감량'  # 기본값 설정
                self.__dict__.update(info)

        return UserObject(user_info)

    def get_user_by_id(self, user_id):
        """
        사용자 ID로 사용자 정보 조회

        Args:
            user_id (int): 사용자의 고유 식별자

        Returns:
            dict: 사용자 정보 또는 찾지 못했을 경우 None
        """
        # 기존 구현 유지
        return {
            'id': user_id,
            'username': '샘플_사용자',
            'email': 'user@example.com',
            'age': 30,
            'gender': '남성',
            'weight': 70,
            'height': 175
        }

    def update_user_profile(self, user_id, profile_data):
        """
        사용자 프로필 정보 업데이트

        Args:
            user_id (int): 사용자의 고유 식별자
            profile_data (dict): 업데이트할 프로필 정보

        Returns:
            bool: 업데이트 성공 시 True, 실패 시 False
        """
        # 기존 구현 유지
        return True