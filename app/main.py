"""
ELBIX AIDD - AI 기반 배전 설계 자동화 시스템
FastAPI 애플리케이션 진입점
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.api.routes import router
from app.api.auth import router as auth_router

# FastAPI 앱 인스턴스 생성
app = FastAPI(
    title=settings.APP_NAME,
    description="AI 기반 배전 설계 자동화 및 공사비 최적 경로 추천 시스템",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 허용 오리진 목록 파싱 (환경 변수에서 쉼표로 구분된 문자열)
cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", settings.CORS_ORIGINS).split(",")
    if origin.strip()
]

# 개발용 오리진은 항상 포함 (배포 무시 시 로컬/192.168.0.64:3000에서 설계·로그인이 동작하도록)
_dev_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://192.168.0.64:3000",
    "http://192.168.0.64:3001",
]
for o in _dev_origins:
    if o not in cors_origins:
        cors_origins.append(o)

# 세션 미들웨어 설정 (쿠키 기반 세션)
# 세션 쿠키는 path="/"로 전체 경로(/api/v1 포함)에 적용됨. 리버스 프록시·서브패스 배포 시에도 동일.
secret_key = os.getenv("SECRET_KEY", settings.SESSION_SECRET_KEY)
https_only = os.getenv("SESSION_HTTPS_ONLY", "False").lower() == "true" or settings.SESSION_HTTPS_ONLY

app.add_middleware(
    SessionMiddleware,
    secret_key=secret_key,
    session_cookie="elbix_session",
    max_age=3600,
    path="/",
    same_site="lax",
    https_only=https_only
)

# CORS 미들웨어 설정
# withCredentials 사용 시 allow_origins에 "*"를 사용할 수 없음
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """서버 기동 시 데이터 캐시 예열 (Warm-up)"""
    import asyncio
    from app.core.wfs_client import WFSClient
    from app.core.preprocessor import DataPreprocessor
    
    print("--- [Warm-up] 초기 데이터 캐시 예열 시작 ---")
    try:
        wfs_client = WFSClient()
        # 충주 중앙부 기본 좌표 (사용자가 처음 보게 될 위치)
        cx, cy = 14242500, 4432200
        
        # 백그라운드에서 초기 데이터 로드 및 계통 분석 수행
        raw_data = await wfs_client.get_all_data(cx, cy, settings.BBOX_SIZE)
        preprocessor = DataPreprocessor()
        preprocessor.process(raw_data)
        
        print(f"--- [Warm-up] 예열 완료: 전주 {len(raw_data['poles'])}개 로드됨 ---")
    except Exception as e:
        print(f"--- [Warm-up] 예열 중 오류 (무시): {e} ---")

@app.get("/")
async def root():
    """루트 엔드포인트 - 서버 상태 확인"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
