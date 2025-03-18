import speech_recognition as sr
# pip install SpeechRecognition
import re

def transcribe_audio(audio_path):
    """
    음성 파일을 텍스트로 변환하는 함수
    :param audio_path: 변환할 오디오 파일의 경로
    :return: 변환된 텍스트
    """
    recognizer = sr.Recognizer()

    try:
        with sr.AudioFile(audio_path) as source:
            recognizer.adjust_for_ambient_noise(source)  # 배경 소음 조정
            audio_data = recognizer.record(source)  # 오디오 데이터 읽기
            transcript = recognizer.recognize_google(audio_data, language="ko-KR")  # 한국어 음성 인식
            return transcript
    except sr.UnknownValueError:
        return "음성을 인식할 수 없습니다."
    except sr.RequestError:
        return "음성 인식 서비스에 연결할 수 없습니다."

def extract_meal_information(transcript):
    """
    변환된 텍스트에서 식사 정보를 추출하는 함수
    :param transcript: 음성 인식된 텍스트
    :return: 추출된 식사 정보 (예: 음식 이름, 시간 등)
    """
    # 정규 표현식을 활용한 간단한 식사 정보 추출 예제
    meal_keywords = ["아침", "점심", "저녁", "간식"]
    food_pattern = r"([가-힣]+(밥|국|김치|찌개|반찬|고기|음료|커피|과일|빵|라면|햄버거|피자|치킨|샐러드))"

    detected_meals = [word for word in meal_keywords if word in transcript]
    detected_foods = re.findall(food_pattern, transcript)

    meal_info = {
        "mealtime": detected_meals[0] if detected_meals else "알 수 없음",
        "foods": [food[0] for food in detected_foods]  # 정규표현식 결과에서 음식 이름만 추출
    }

    return meal_info if meal_info["foods"] else None
