"""
ELBIX AIDD 응답 모델 v2
- API 응답 데이터 구조 정의
- 전압강하, 용량이용률, 상세 비용 정보 추가
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class DesignStatus(str, Enum):
    """설계 상태"""
    SUCCESS = "Success"
    FAILED = "Failed"
    NO_ROUTE = "NoRoute"
    OVER_DISTANCE = "OverDistance"


class CostDetailItem(BaseModel):
    """비용 상세 항목"""
    count: Optional[int] = Field(default=None, description="수량")
    length: Optional[float] = Field(default=None, description="길이(m)")
    spec: Optional[str] = Field(default=None, description="규격")
    unit_cost: Optional[int] = Field(default=None, description="단가(원)")
    cost: int = Field(default=0, description="비용(원)")


class MaterialCostDetail(BaseModel):
    """재료비 상세"""
    pole: CostDetailItem = Field(default_factory=CostDetailItem, description="전주")
    wire: CostDetailItem = Field(default_factory=CostDetailItem, description="전선")
    insulator: CostDetailItem = Field(default_factory=CostDetailItem, description="애자")
    arm_tie: CostDetailItem = Field(default_factory=CostDetailItem, description="완금")
    clamp: CostDetailItem = Field(default_factory=CostDetailItem, description="클램프")
    connector: CostDetailItem = Field(default_factory=CostDetailItem, description="접속자재")
    total: int = Field(default=0, description="재료비 합계")


class LaborCostDetail(BaseModel):
    """인건비 상세"""
    pole_install: CostDetailItem = Field(default_factory=CostDetailItem, description="전주 설치")
    wire_stretch: CostDetailItem = Field(default_factory=CostDetailItem, description="전선 가선")
    insulator_install: CostDetailItem = Field(default_factory=CostDetailItem, description="애자 설치")
    base: int = Field(default=0, description="기본 노무비")
    total: int = Field(default=0, description="인건비 합계")


class DetailedCostBreakdown(BaseModel):
    """상세 비용 분석"""
    material: MaterialCostDetail = Field(default_factory=MaterialCostDetail, description="재료비")
    labor: LaborCostDetail = Field(default_factory=LaborCostDetail, description="인건비")
    overhead_rate: float = Field(default=0.15, description="경비율")
    overhead_cost: int = Field(default=0, description="경비")
    profit_rate: float = Field(default=0.10, description="이윤율")
    profit_cost: int = Field(default=0, description="이윤")
    extra_cost: int = Field(default=0, description="추가 비용")
    extra_detail: Optional[str] = Field(default=None, description="추가 비용 상세")
    subtotal: int = Field(default=0, description="소계(재료비+인건비)")
    total: int = Field(default=0, description="총 비용")


class VoltageDropInfo(BaseModel):
    """전압 강하 정보"""
    distance_m: float = Field(default=0, description="거리(m)")
    load_kw: float = Field(default=0, description="부하(kW)")
    voltage_drop_v: float = Field(default=0, description="전압 강하(V)")
    voltage_drop_percent: float = Field(default=0, description="전압 강하율(%)")
    is_acceptable: bool = Field(default=True, description="허용 범위 내 여부")
    limit_percent: float = Field(default=6.0, description="허용 한계(%)")
    wire_spec: Optional[str] = Field(default=None, description="전선 규격")
    message: Optional[str] = Field(default=None, description="결과 메시지")


class CapacityInfo(BaseModel):
    """변압기 용량 정보"""
    transformer_id: Optional[str] = Field(default=None, description="변압기 ID")
    capacity_kva: float = Field(default=0, description="변압기 용량(kVA)")
    current_load_kva: float = Field(default=0, description="현재 부하(kVA)")
    requested_load_kva: float = Field(default=0, description="신청 부하(kVA)")
    total_load_kva: float = Field(default=0, description="신청 후 총 부하(kVA)")
    utilization_rate: float = Field(default=0, description="이용률(0.0~1.0)")
    available_capacity_kva: float = Field(default=0, description="가용 용량(kVA)")
    is_valid: bool = Field(default=True, description="용량 적합 여부")
    is_warning: bool = Field(default=False, description="경고 수준(75% 초과)")
    message: Optional[str] = Field(default=None, description="결과 메시지")
    recommended_capacity_kva: Optional[float] = Field(default=None, description="추천 용량(kVA)")


class RouteResult(BaseModel):
    """개별 경로 결과"""
    
    # 순위 (cost_index 기준)
    rank: int = Field(
        ...,
        description="경로 순위 (cost_index 기준, 1이 최저 비용)",
        ge=1
    )
    
    # 예상 공사비 (원)
    total_cost: int = Field(
        ...,
        description="예상 총 공사비 (원)",
        ge=0
    )
    
    # PRD 4.2 공사비 환산 점수
    cost_index: int = Field(
        default=0,
        description="공사비 환산 점수 (PRD 4.2: N_poles×10000 + D×1 + N_turns×50)",
        ge=0
    )
    
    # 총 경로 거리 (m)
    total_distance: float = Field(
        ...,
        description="총 경로 거리 (미터)",
        ge=0
    )
    
    # 시작 기설전주 ID
    start_pole_id: str = Field(
        ...,
        description="시작 기설전주 ID"
    )
    
    # 시작 기설전주 좌표
    start_pole_coord: List[float] = Field(
        ...,
        description="시작 기설전주 좌표 [x, y]"
    )
    
    # 신설 전주 개수
    new_poles_count: int = Field(
        ...,
        description="신설 전주 개수",
        ge=0
    )
    
    # 전체 경로 좌표 (LineString)
    path_coordinates: List[List[float]] = Field(
        ...,
        description="전체 경로 좌표 [[x1, y1], [x2, y2], ...]"
    )
    
    # 신설 전주 좌표
    new_pole_coordinates: List[List[float]] = Field(
        default=[],
        description="신설 전주 좌표 [[px1, py1], [px2, py2], ...]"
    )
    
    # 전선 비용
    wire_cost: int = Field(
        default=0,
        description="전선 비용 (원)"
    )
    
    # 전주 비용
    pole_cost: int = Field(
        default=0,
        description="신설 전주 비용 (원)"
    )
    
    # 노무비
    labor_cost: int = Field(
        default=0,
        description="노무비 (원)"
    )
    
    # 비고 (Fast Track 등)
    remark: Optional[str] = Field(
        default=None,
        description="비고 (예: FastTrack - 50m 이내 직접 연결)"
    )
    
    # ===== v2 추가 필드 =====
    
    # 상세 비용 분석
    detailed_cost: Optional[DetailedCostBreakdown] = Field(
        default=None,
        description="상세 비용 분석"
    )
    
    # 전압 강하 정보
    voltage_drop: Optional[VoltageDropInfo] = Field(
        default=None,
        description="전압 강하 정보"
    )
    
    # 변압기 용량 정보
    capacity_info: Optional[CapacityInfo] = Field(
        default=None,
        description="변압기 용량 정보"
    )
    
    # 전주 규격
    pole_spec: Optional[str] = Field(
        default=None,
        description="전주 규격 (C10/C12/STEEL_10 등)"
    )
    
    # 전선 규격
    wire_spec: Optional[str] = Field(
        default=None,
        description="전선 규격 (OW_22/ACSR_95 등)"
    )
    
    # 기설 전주 전압 정보 (고압/저압)
    source_voltage_type: Optional[str] = Field(
        default=None,
        description="기설 전주 전압 유형 (HV: 고압, LV: 저압)"
    )
    
    # 기설 전주 상 정보 (단상/3상)
    source_phase_type: Optional[str] = Field(
        default=None,
        description="기설 전주 상 유형 (1: 단상, 3: 3상)"
    )


class DesignResponse(BaseModel):
    """배전 설계 응답 모델"""
    
    # 처리 상태
    status: DesignStatus = Field(
        ...,
        description="처리 상태"
    )
    
    # 요청 규격 (한글)
    request_spec: str = Field(
        ...,
        description="요청 규격 (단상/3상)"
    )
    
    # 수용가 좌표
    consumer_coord: List[float] = Field(
        ...,
        description="수용가 좌표 [x, y]"
    )
    
    # 탐색된 경로 목록 (공사비 순)
    routes: List[RouteResult] = Field(
        default=[],
        description="경로 목록 (공사비 오름차순)"
    )
    
    # 오류 메시지 (실패 시)
    error_message: Optional[str] = Field(
        default=None,
        description="오류 메시지 (실패 시)"
    )
    
    # 처리 시간 (ms)
    processing_time_ms: Optional[int] = Field(
        default=None,
        description="처리 시간 (밀리초)"
    )
    
    # ===== v2 추가 필드 =====
    
    # 요청 부하 (kW)
    requested_load_kw: Optional[float] = Field(
        default=None,
        description="요청 부하 (kW)"
    )
    
    # 메타데이터
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="추가 메타데이터 (후보 전주 목록 등)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "Success",
                "request_spec": "3상",
                "consumer_coord": [14241940.81, 4437601.67],
                "routes": [
                    {
                        "rank": 1,
                        "total_cost": 1500000,
                        "cost_index": 30120,
                        "total_distance": 120.5,
                        "start_pole_id": "POLE_12345",
                        "start_pole_coord": [14241850.0, 4437550.0],
                        "new_poles_count": 3,
                        "path_coordinates": [
                            [14241940.81, 4437601.67],
                            [14241900.0, 4437580.0],
                            [14241850.0, 4437550.0]
                        ],
                        "new_pole_coordinates": [
                            [14241920.0, 4437590.0],
                            [14241880.0, 4437570.0],
                            [14241860.0, 4437560.0]
                        ],
                        "wire_cost": 600000,
                        "pole_cost": 700000,
                        "labor_cost": 200000,
                        "pole_spec": "C10",
                        "wire_spec": "OW_22",
                        "voltage_drop": {
                            "distance_m": 120.5,
                            "load_kw": 5.0,
                            "voltage_drop_v": 4.2,
                            "voltage_drop_percent": 1.9,
                            "is_acceptable": True,
                            "limit_percent": 6.0
                        }
                    }
                ],
                "processing_time_ms": 1250,
                "requested_load_kw": 5.0
            }
        }
