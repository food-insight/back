import os
from PIL import Image
import io
import uuid
from werkzeug.utils import secure_filename

def is_allowed_image(filename: str) -> bool:
    """
    허용된 이미지 파일 확장자인지 확인

    Args:
        filename (str): 파일 이름

    Returns:
        bool: 허용된 이미지 파일이면 True, 아니면 False
    """
    # 허용된 이미지 확장자 목록
    ALLOWED_EXTENSIONS = {
        'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'
    }

    # 파일 확장자 추출 (대소문자 구분 없이)
    return filename.lower().split('.')[-1] in ALLOWED_EXTENSIONS

def process_image(image_file, max_size=(800, 800), max_file_size=5*1024*1024):
    """
    이미지 전처리 함수

    Args:
        image_file: 업로드된 이미지 파일
        max_size (tuple): 최대 이미지 크기 (너비, 높이)
        max_file_size (int): 최대 파일 크기 (바이트)

    Returns:
        bytes: 처리된 이미지 바이트
    """
    try:
        # 이미지 열기
        with Image.open(image_file) as img:
            # 이미지 파일 크기 확인
            file_size = len(image_file.read())
            image_file.seek(0)  # 파일 포인터 초기화

            if file_size > max_file_size:
                raise ValueError(f"이미지 크기가 너무 큽니다. 최대 {max_file_size/1024/1024}MB까지 허용됩니다.")

            # 이미지 포맷 확인 및 변환
            if img.format not in ['JPEG', 'PNG', 'GIF']:
                img = img.convert('RGB')

            # 이미지 크기 조정
            img.thumbnail(max_size, Image.LANCZOS)

            # 이미지를 바이트로 변환
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            processed_image = buffer.getvalue()

            return processed_image

    except Exception as e:
        raise ValueError(f"이미지 처리 중 오류 발생: {str(e)}")

def validate_food_image(image_file):
    """
    음식 이미지 유효성 검사

    Args:
        image_file: 업로드된 이미지 파일

    Returns:
        bool: 유효한 음식 이미지이면 True, 아니면 False
    """
    try:
        # 이미지 열기
        with Image.open(image_file) as img:
            # 기본적인 이미지 품질 검사
            # 예: 최소 크기, 해상도 등
            width, height = img.size

            # 최소 크기 제한 (예: 100x100 픽셀)
            if width < 100 or height < 100:
                return False

            # 추가 검사 로직 (필요시 확장)
            # 예: 색상 분포, 엣지 검출 등 고급 이미지 분석

            return True

    except Exception:
        return False


def save_image(image_file, upload_folder, subfolder='', prefix=''):
    """
    이미지 파일을 서버에 저장

    Args:
        image_file: 업로드된 이미지 파일
        upload_folder (str): 기본 업로드 폴더 경로
        subfolder (str, optional): 하위 폴더 경로. 기본값은 빈 문자열
        prefix (str, optional): 파일명 접두사. 기본값은 빈 문자열

    Returns:
        tuple: (저장된 파일 경로, 파일명)
    """
    try:
        # 고유한 파일명 생성
        filename = secure_filename(f"{prefix}{uuid.uuid4()}_{image_file.filename}")

        # 저장 경로 생성 (하위 폴더 포함)
        save_path = os.path.join(upload_folder, subfolder)
        os.makedirs(save_path, exist_ok=True)

        # 전체 파일 경로
        full_path = os.path.join(save_path, filename)

        # 이미지 저장
        image_file.save(full_path)

        return full_path, filename

    except Exception as e:
        raise ValueError(f"이미지 저장 중 오류 발생: {str(e)}")