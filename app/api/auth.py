"""
ELBIX AIDD 인증 라우터
- 관리자 로그인/로그아웃 처리
- 세션 기반 인증
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel

from app.config import settings
from app.models.request import LoginRequest

logger = logging.getLogger(__name__)

# 개발 전용: DEBUG일 때 이 헤더가 있으면 세션 없이 admin으로 인정 (쿠키/프록시 이슈 우회)
DEV_AUTH_HEADER = "X-Dev-Auth"
DEV_AUTH_VALUE = "admin"

# 인증 라우터 생성
router = APIRouter(prefix="/auth", tags=["auth"])

# 관리자 계정 (하드코딩 - 실제 운영환경에서는 환경변수나 DB 사용 권장)
ADMIN_CREDENTIALS = {
    "username": "admin",
    "password": "admin123"
}


class LoginResponse(BaseModel):
    """로그인 응답 모델"""
    success: bool
    message: str
    username: Optional[str] = None


class AuthStatusResponse(BaseModel):
    """인증 상태 응답 모델 (Pydantic v2 호환)"""
    authenticated: bool
    username: Optional[str] = None


def require_auth(request: Request):
    """
    인증 의존성 함수
    - 로그인되지 않은 경우 401 에러 반환
    - 개발 전용: DEBUG=True일 때 X-Dev-Auth: admin 헤더가 있으면 세션 없이 인정 (쿠키 이슈 우회)
    """
    # 개발 전용 우회: DEBUG일 때만 허용, 배포 시에는 사용하지 않음
    if getattr(settings, "DEBUG", False) and request.headers.get(DEV_AUTH_HEADER) == DEV_AUTH_VALUE:
        return DEV_AUTH_VALUE
    if not request.session.get("authenticated"):
        has_cookie = bool(request.headers.get("cookie"))
        logger.debug("require_auth: 미인증, Cookie 헤더 존재 여부=%s, path=%s", has_cookie, request.url.path)
        raise HTTPException(
            status_code=401,
            detail="로그인이 필요합니다"
        )
    return request.session.get("username")


@router.post("/login", response_model=LoginResponse)
async def login(request: Request, credentials: LoginRequest):
    """
    관리자 로그인
    
    - ID와 비밀번호를 확인하여 세션에 인증 정보 저장
    - 성공 시 세션 쿠키 발급
    """
    # 관리자 계정 확인
    if (credentials.username == ADMIN_CREDENTIALS["username"] and 
        credentials.password == ADMIN_CREDENTIALS["password"]):
        
        # 세션에 인증 정보 저장
        request.session["authenticated"] = True
        request.session["username"] = credentials.username
        
        return LoginResponse(
            success=True,
            message="로그인 성공",
            username=credentials.username
        )
    else:
        raise HTTPException(
            status_code=401,
            detail="아이디 또는 비밀번호가 올바르지 않습니다"
        )


@router.post("/logout", response_model=LoginResponse)
async def logout(request: Request):
    """
    로그아웃
    
    - 세션 정보 삭제
    """
    username = request.session.get("username")
    
    # 세션 클리어
    request.session.clear()
    
    return LoginResponse(
        success=True,
        message="로그아웃 되었습니다",
        username=username
    )


@router.get("/me", response_model=AuthStatusResponse)
async def get_current_user(request: Request):
    """
    현재 로그인 상태 확인
    
    - 로그인 여부와 사용자 정보 반환
    - 세션/쿠키 오류 시 500 대신 200 + authenticated=False 로 응답해 프론트 연동이 끊기지 않게 함
    - 개발 전용: DEBUG일 때 X-Dev-Auth: admin 이 있으면 authenticated=True 로 응답 (쿠키 이슈 우회)
    """
    try:
        # 개발 전용 우회: DEBUG일 때 헤더로 인정
        if getattr(settings, "DEBUG", False) and request.headers.get(DEV_AUTH_HEADER) == DEV_AUTH_VALUE:
            return AuthStatusResponse(authenticated=True, username=DEV_AUTH_VALUE)
        authenticated = request.session.get("authenticated", False)
        username = request.session.get("username")
        return AuthStatusResponse(
            authenticated=bool(authenticated),
            username=str(username) if authenticated and username else None
        )
    except Exception as e:
        logger.warning("get_current_user 예외(세션/쿠키 문제 가능): %s", e, exc_info=True)
        return AuthStatusResponse(authenticated=False, username=None)
