import speech_recognition as sr
import re
from fuzzywuzzy import process  # 유사 단어 매칭 라이브러리
# pip install SpeechRecognition fuzzywuzzy

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
    # 식사 시간 키워드 
    meal_keywords = {
        "아침": ["아침", "아침밥", "모닝"],
        "점심": ["점심", "점심밥", "런치"],
        "저녁": ["저녁", "저녁밥", "디너"],
        "간식": ["간식", "스낵", "야식"]
    }

    # 식사 시간 감지 (단순 키워드 포함뿐만 아니라 유사 문장도 분석)
    detected_mealtime = None
    for mealtime, keywords in meal_keywords.items():
        for keyword in keywords:
            if keyword in transcript:
                detected_mealtime = mealtime
                break
        if detected_mealtime:
            break

    # 음식 리스트
    known_foods = [
        "바나나", "우유", "사과", "밥", "김치", "계란", "닭가슴살", "고구마", "샐러드", "토스트",
        "고기", "스테이크", "토마토", "치킨", "떡볶이", "라면", "샌드위치", "수박", "오렌지",
        "커피", "햄버거", "피자", "오트밀", "두부", "된장국", "불고기", "파스타", "떡국", "만두"
    ]

    # 유사 단어 매칭을 활용한 음식 검출
    detected_foods = []
    for word in transcript.split():
        match, score = process.extractOne(word, known_foods)  # 가장 유사한 음식 찾기
        if score > 80:  # 유사도가 80 이상이면 유효한 음식으로 간주
            detected_foods.append(match)

    # 음식이 하나도 없을 경우 예외 처리
    if not detected_foods:
        return None

    return {"mealtime": detected_mealtime if detected_mealtime else "알 수 없음", "foods": detected_foods}
