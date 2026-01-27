"""
ELBIX AIDD 요청 모델
- API 요청 데이터 검증 및 파싱
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional

from app.config import settings


class LoginRequest(BaseModel):
    """로그인 요청 모델"""
    
    username: str = Field(
        ...,
        description="사용자 ID",
        min_length=1,
        max_length=50
    )
    
    password: str = Field(
        ...,
        description="비밀번호",
        min_length=1,
        max_length=100
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "password": "admin123"
            }
        }


class DesignRequest(BaseModel):
    """배전 설계 요청 모델"""
    
    # 입력 타입 (기본: 좌표)
    code: str = Field(
        default="coord",
        description="입력 타입 (coord: 좌표)"
    )
    
    # 수용가 좌표 (EPSG:3857, "x,y" 형식)
    coord: str = Field(
        ...,
        description="수용가 좌표 (EPSG:3857, 'x,y' 형식)",
        examples=["14241940.817790061,4437601.6755945515"]
    )
    
    # 신청 규격 (1: 단상, 3: 3상)
    phase_code: str = Field(
        default=settings.PHASE_SINGLE,
        description="신청 규격 ('1': 단상, '3': 3상)"
    )
    
    # VWorld API 키 (선택)
    vworld_key: Optional[str] = Field(
        default=None,
        description="VWorld API 키"
    )
    
    # WFS URL 오버라이드 (선택)
    gis_wfs_url: Optional[str] = Field(
        default=None,
        description="GIS WFS 서버 URL (기본값 사용 시 생략)"
    )
    
    base_wfs_url: Optional[str] = Field(
        default=None,
        description="BASE WFS 서버 URL (기본값 사용 시 생략)"
    )
    
    view_wfs_url: Optional[str] = Field(
        default=None,
        description="VIEW WFS 서버 URL (기본값 사용 시 생략)"
    )
    
    eps_url: Optional[str] = Field(
        default=None,
        description="EPS 서버 URL (기본값 사용 시 생략)"
    )
    
    @field_validator('coord')
    @classmethod
    def validate_coord(cls, v: str) -> str:
        """좌표 형식 검증"""
        try:
            parts = v.split(',')
            if len(parts) != 2:
                raise ValueError("좌표는 'x,y' 형식이어야 합니다")
            
            x = float(parts[0].strip())
            y = float(parts[1].strip())
            
            # EPSG:3857 좌표 범위 검증 (대략적인 한국 영역)
            # X: 약 14,000,000 ~ 15,000,000
            # Y: 약 4,000,000 ~ 5,000,000
            if not (13000000 < x < 16000000):
                raise ValueError(f"X 좌표가 유효 범위를 벗어났습니다: {x}")
            if not (3500000 < y < 5500000):
                raise ValueError(f"Y 좌표가 유효 범위를 벗어났습니다: {y}")
                
            return v
        except ValueError as e:
            raise ValueError(f"좌표 형식 오류: {str(e)}")
    
    @field_validator('phase_code')
    @classmethod
    def validate_phase_code(cls, v: str) -> str:
        """상 코드 검증"""
        valid_codes = [settings.PHASE_SINGLE, settings.PHASE_THREE]
        if v not in valid_codes:
            raise ValueError(f"상 코드는 {valid_codes} 중 하나여야 합니다")
        return v
    
    def get_coord_tuple(self) -> tuple[float, float]:
        """좌표를 tuple로 반환"""
        parts = self.coord.split(',')
        return (float(parts[0].strip()), float(parts[1].strip()))
    
    def get_phase_name(self) -> str:
        """상 이름 반환 (한글)"""
        return "3상" if self.phase_code == settings.PHASE_THREE else "단상"
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "coord",
                "coord": "14241940.817790061,4437601.6755945515",
                "phase_code": "3"
            }
        }
