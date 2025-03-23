# 미니프로젝트 3 백엔드
### 작성 팀원 : 구강현, 김태기, 이윤화

## 실행 전 필요 파일
- .env
    - OPENAI_API_KEY = 본인 키

# 영양분석을 통한 식단 관리 웹 API 문서

이 프로젝트는 사용자의 식단, 음성, 이미지, 텍스트 정보를 활용하여 개인화된 건강 식단 추천과 영양 분석을 제공합니다.

---

## 📁 주요 API 라우트별 분류

### 🔐 Auth (회원가입 및 로그인)
- `POST /auth/register` : 사용자 회원가입
- `POST /auth/login` : 로그인 및 토큰 발급
- `POST /auth/refresh` : 액세스 토큰 갱신
- `POST /auth/logout` : 로그아웃

---

### 👤 User (프로필 및 알레르기)
- `GET /user/profile` : 사용자 프로필 조회
- `PUT /user/profile` : 사용자 프로필 수정
- `GET /user/allergies` : 사용자 알레르기 목록 조회
- `POST /user/allergies` : 알레르기 추가
- `DELETE /user/allergies/<allergy_id>` : 알레르기 삭제
- `PUT /user/health-goal` : 건강 목표 수정
- `GET /user/dashboard` : 사용자 요약 대시보드

---

### 🍽️ Meal (식사 기록)
- `POST /meal/upload` : 식사 이미지 업로드
- `POST /meal/` : 식사 기록 추가
- `GET /meal/` : 식사 기록 목록 조회 (필터/페이징)
- `GET /meal/<meal_id>` : 식사 상세 조회
- `PUT /meal/<meal_id>` : 식사 수정
- `DELETE /meal/<meal_id>` : 식사 삭제
- `GET /meal/statistics` : 통계 조회 (일/주/월)

---

### 🧠 Nutrition (영양 분석)
- `GET /nutrition/analyze/<meal_id>` : 식사별 영양 분석

---

### 🧠 Chatbot (영양 챗봇)
- `POST /chatbot/api/chat` : 사용자 메시지를 기반으로 대화 및 추천 응답

---

### 🎙 Speech (음성 기반 입력)
- `POST /speech/transcribe` : 음성을 텍스트로 변환
- `POST /speech/meal-record` : 음성을 통한 식사 정보 추출
- `POST /speech/recognize-food` : 음성에서 음식 이름 추출

---

### 🧪 Recommendation (식단 추천)
- `GET /recommendation/meal` : 맞춤형 식단 추천
- `POST /recommendation/alternatives` : 대체 음식 추천
- `GET /recommendation/recipes` : 레시피 추천 (RAG 활용)
- `GET /recommendation/history` : 추천 이력

---

### 🖼️ Image (이미지 업로드 및 음식 인식)
- `POST /image/upload` : 이미지 업로드 및 식사 기록 연결
- `GET /image/view/<filename>` : 이미지 조회
- `POST /image/food-recognition` : 음식 이미지 인식

---

### 🤖 Recognition (외부 이미지/텍스트 기반 음식 인식)
- `POST /recognition/` : 이미지 또는 텍스트 기반 음식 인식

---

## 🗂️ 인증 정보
- 대부분의 API는 JWT 인증 필요 (`@jwt_required()`)
- 로그인 시 `Authorization`, `Refresh-Token` 헤더로 토큰 제공

## ⚠️ 오류 응답 예시
```json
{
  "success": false,
  "message": "오류 메시지",
  "code": 400
}
```

---

## 🧪 개발 및 테스트 환경
- Flask, Flask-JWT-Extended, SQLAlchemy
- OpenAI GPT (RAG), 음성 인식 및 이미지 인식 서비스 포함

---

## 사용 데이터 출처
- korean_foods_processed.csv 출처
    - 공공데이터 포털 : 전국통합식품영양성분정보(음식)표준데이터터
    - https://www.data.go.kr/data/15100070/standard.do#tab_layer_grid
