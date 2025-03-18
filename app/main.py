from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 더미 라우터 임포트
from app.routers import dummy

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="영양 인사이트 API",
    description="식단 분석 및 건강 식품 추천 서비스 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 루트 엔드포인트
@app.get("/", tags=["일반"])
async def root():
    """API 서버 상태 확인"""
    return {"status": "online", "message": "영양 인사이트 API가 정상 작동 중입니다."}

# 테스트 코드에서 사용하는 엔드포인트를 위한 더미 라우터 등록
app.include_router(dummy.router, prefix="/api/foods", tags=["음식 인식"])
app.include_router(dummy.router, prefix="/api/nutrition", tags=["영양 분석"])
app.include_router(dummy.router, prefix="/api/meals", tags=["식사 관리"])
app.include_router(dummy.router, prefix="/api/users", tags=["사용자 관리"])
app.include_router(dummy.router, prefix="/api/recommendations", tags=["추천"])
app.include_router(dummy.router, prefix="/api/chat", tags=["챗봇"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)