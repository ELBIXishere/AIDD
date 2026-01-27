"""
ELBIX AIDD 공사비 계산 모듈 v2
- 상세 공사비 산출: 전주/전선 규격별, 부자재, 인건비, 경비
- 기존 호환성 유지
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

from app.config import settings
from app.core.pole_allocator import AllocationResult, NewPole
from app.core.pathfinder import PathResult

logger = logging.getLogger(__name__)


# ===== 전주/전선 규격 열거형 =====
class PoleSpec(Enum):
    """전주 규격"""
    C10 = "C10"          # C종 10m 콘크리트
    C12 = "C12"          # C종 12m 콘크리트
    C14 = "C14"          # C종 14m 콘크리트
    STEEL_10 = "STEEL_10"  # 강관 10m
    STEEL_12 = "STEEL_12"  # 강관 12m
    DEFAULT = "DEFAULT"    # 기본값


class WireSpec(Enum):
    """전선 규격"""
    ACSR_58 = "ACSR_58"     # ACSR 58mm²
    ACSR_95 = "ACSR_95"     # ACSR 95mm²
    ACSR_160 = "ACSR_160"   # ACSR 160mm²
    OW_22 = "OW_22"         # OW 22mm²
    OW_38 = "OW_38"         # OW 38mm²
    DEFAULT = "DEFAULT"      # 기본값


# ===== 규격별 단가 매핑 =====
POLE_COST_MAP = {
    PoleSpec.C10: settings.COST_POLE_C10,
    PoleSpec.C12: settings.COST_POLE_C12,
    PoleSpec.C14: settings.COST_POLE_C14,
    PoleSpec.STEEL_10: settings.COST_POLE_STEEL_10,
    PoleSpec.STEEL_12: settings.COST_POLE_STEEL_12,
    PoleSpec.DEFAULT: settings.COST_POLE,
}

WIRE_COST_MAP = {
    WireSpec.ACSR_58: settings.COST_WIRE_ACSR_58,
    WireSpec.ACSR_95: settings.COST_WIRE_ACSR_95,
    WireSpec.ACSR_160: settings.COST_WIRE_ACSR_160,
    WireSpec.OW_22: settings.COST_WIRE_OW_22,
    WireSpec.OW_38: settings.COST_WIRE_OW_38,
    WireSpec.DEFAULT: settings.COST_WIRE_LV,
}


@dataclass
class MaterialCost:
    """재료비 상세"""
    # 전주
    pole_count: int = 0
    pole_spec: str = "C10"
    pole_unit_cost: int = 0
    pole_cost: int = 0
    
    # 전선
    wire_length: float = 0.0
    wire_spec: str = "OW_22"
    wire_unit_cost: int = 0
    wire_cost: int = 0
    
    # 부자재
    insulator_count: int = 0
    insulator_cost: int = 0
    arm_tie_count: int = 0
    arm_tie_cost: int = 0
    clamp_count: int = 0
    clamp_cost: int = 0
    connector_count: int = 0
    connector_cost: int = 0
    
    # 재료비 합계
    total: int = 0
    
    def calculate_total(self):
        """재료비 합계 계산"""
        self.total = (
            self.pole_cost +
            self.wire_cost +
            self.insulator_cost +
            self.arm_tie_cost +
            self.clamp_cost +
            self.connector_cost
        )


@dataclass
class LaborCost:
    """인건비 상세"""
    # 전주 설치
    pole_install_count: int = 0
    pole_install_unit_cost: int = 0
    pole_install_cost: int = 0
    
    # 전선 가선
    wire_stretch_length: float = 0.0
    wire_stretch_unit_cost: int = 0
    wire_stretch_cost: int = 0
    
    # 애자 설치
    insulator_install_count: int = 0
    insulator_install_unit_cost: int = 0
    insulator_install_cost: int = 0
    
    # 기본 노무비
    base_labor_cost: int = 0
    
    # 인건비 합계
    total: int = 0
    
    def calculate_total(self):
        """인건비 합계 계산"""
        self.total = (
            self.base_labor_cost +
            self.pole_install_cost +
            self.wire_stretch_cost +
            self.insulator_install_cost
        )


@dataclass
class CostBreakdown:
    """비용 명세 (기존 호환성 유지)"""
    wire_cost: int = 0        # 전선 비용
    pole_cost: int = 0        # 전주 비용
    labor_cost: int = 0       # 노무비
    extra_cost: int = 0       # 추가 비용 (도로 횡단 등)
    total_cost: int = 0       # 총 비용
    
    def calculate_total(self):
        """총 비용 계산"""
        self.total_cost = (
            self.wire_cost + 
            self.pole_cost + 
            self.labor_cost + 
            self.extra_cost
        )


@dataclass
class DetailedCostBreakdown:
    """상세 비용 명세"""
    # 상세 항목
    material: MaterialCost = field(default_factory=MaterialCost)
    labor: LaborCost = field(default_factory=LaborCost)
    
    # 경비
    overhead_rate: float = 0.15  # 경비율
    overhead_cost: int = 0
    
    # 이윤
    profit_rate: float = 0.10   # 이윤율
    profit_cost: int = 0
    
    # 도로 횡단 등 추가 비용
    extra_cost: int = 0
    extra_detail: str = ""
    
    # 합계
    subtotal: int = 0          # 재료비 + 인건비
    total_cost: int = 0        # 총 비용
    
    def calculate_all(self):
        """모든 비용 계산"""
        self.material.calculate_total()
        self.labor.calculate_total()
        
        # 소계 (재료비 + 인건비)
        self.subtotal = self.material.total + self.labor.total
        
        # 경비 (소계의 일정 비율)
        self.overhead_cost = int(self.subtotal * self.overhead_rate)
        
        # 이윤 (소계의 일정 비율)
        self.profit_cost = int(self.subtotal * self.profit_rate)
        
        # 총 비용
        self.total_cost = (
            self.subtotal +
            self.overhead_cost +
            self.profit_cost +
            self.extra_cost
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환 (API 응답용)"""
        return {
            "material": {
                "pole": {
                    "count": self.material.pole_count,
                    "spec": self.material.pole_spec,
                    "unit_cost": self.material.pole_unit_cost,
                    "cost": self.material.pole_cost
                },
                "wire": {
                    "length": round(self.material.wire_length, 1),
                    "spec": self.material.wire_spec,
                    "unit_cost": self.material.wire_unit_cost,
                    "cost": self.material.wire_cost
                },
                "accessories": {
                    "insulator": {
                        "count": self.material.insulator_count,
                        "cost": self.material.insulator_cost
                    },
                    "arm_tie": {
                        "count": self.material.arm_tie_count,
                        "cost": self.material.arm_tie_cost
                    },
                    "clamp": {
                        "count": self.material.clamp_count,
                        "cost": self.material.clamp_cost
                    },
                    "connector": {
                        "count": self.material.connector_count,
                        "cost": self.material.connector_cost
                    }
                },
                "total": self.material.total
            },
            "labor": {
                "pole_install": {
                    "count": self.labor.pole_install_count,
                    "unit_cost": self.labor.pole_install_unit_cost,
                    "cost": self.labor.pole_install_cost
                },
                "wire_stretch": {
                    "length": round(self.labor.wire_stretch_length, 1),
                    "unit_cost": self.labor.wire_stretch_unit_cost,
                    "cost": self.labor.wire_stretch_cost
                },
                "insulator_install": {
                    "count": self.labor.insulator_install_count,
                    "unit_cost": self.labor.insulator_install_unit_cost,
                    "cost": self.labor.insulator_install_cost
                },
                "base": self.labor.base_labor_cost,
                "total": self.labor.total
            },
            "overhead": {
                "rate": self.overhead_rate,
                "cost": self.overhead_cost
            },
            "profit": {
                "rate": self.profit_rate,
                "cost": self.profit_cost
            },
            "extra": {
                "cost": self.extra_cost,
                "detail": self.extra_detail
            },
            "subtotal": self.subtotal,
            "total": self.total_cost
        }


@dataclass
class CostResult:
    """공사비 계산 결과"""
    allocation_result: AllocationResult  # 배치 결과
    cost_breakdown: CostBreakdown = field(default_factory=CostBreakdown)
    detailed_breakdown: Optional[DetailedCostBreakdown] = None  # 상세 비용
    rank: int = 0                        # 순위 (비용 기준)
    
    # 요약 정보
    total_cost: int = 0
    total_distance: float = 0.0
    new_poles_count: int = 0
    start_pole_id: str = ""
    start_pole_coord: Tuple[float, float] = (0, 0)
    path_coordinates: List[List[float]] = field(default_factory=list)
    new_pole_coordinates: List[List[float]] = field(default_factory=list)
    remark: Optional[str] = None
    
    # PRD 4.2 경로 평가 점수 (cost_index)
    # Score = N_poles × W_pole + D × W_dist + N_turns × W_turn
    cost_index: int = 0                  # 공사비 환산 점수
    turn_count: int = 0                  # 굴절 횟수


class CostCalculator:
    """공사비 계산기 v2 - 상세 공사비 산출 지원"""
    
    def __init__(
        self,
        wire_cost_per_meter: int = None,
        pole_cost: int = None,
        labor_base_cost: int = None,
        road_crossing_cost: int = None,
        # 상세 계산 옵션
        pole_spec: PoleSpec = PoleSpec.C10,
        wire_spec: WireSpec = WireSpec.OW_22,
        detailed_mode: bool = True
    ):
        """
        Args:
            wire_cost_per_meter: 전선 단가 (원/m) - 기본 모드용
            pole_cost: 전주 단가 (원/개) - 기본 모드용
            labor_base_cost: 기본 노무비 (원)
            road_crossing_cost: 도로 횡단 추가 비용 (원/회)
            pole_spec: 전주 규격 (상세 모드)
            wire_spec: 전선 규격 (상세 모드)
            detailed_mode: 상세 계산 모드 활성화
        """
        # 기본 단가 (기존 호환성)
        self.wire_cost_per_meter = wire_cost_per_meter or settings.COST_WIRE_LV
        self.pole_cost = pole_cost or settings.COST_POLE
        self.labor_base_cost = labor_base_cost or settings.COST_LABOR_BASE
        self.road_crossing_cost = road_crossing_cost or settings.COST_ROAD_CROSSING
        
        # 상세 계산용
        self.pole_spec = pole_spec
        self.wire_spec = wire_spec
        self.detailed_mode = detailed_mode
    
    def calculate(self, allocation_result: AllocationResult) -> CostResult:
        """
        공사비 계산
        
        Args:
            allocation_result: 전주 배치 결과
        
        Returns:
            공사비 계산 결과
        """
        path_result = allocation_result.path_result
        new_poles = allocation_result.new_poles
        poles_count = len(new_poles)
        wire_length = allocation_result.total_wire_length
        
        result = CostResult(
            allocation_result=allocation_result
        )
        
        # 기본 비용 계산 (기존 호환성)
        breakdown = self._calculate_basic(new_poles, wire_length)
        
        # 상세 비용 계산
        detailed = None
        if self.detailed_mode:
            detailed = self._calculate_detailed(new_poles, wire_length)
            # 상세 계산 결과로 총 비용 업데이트
            breakdown.total_cost = detailed.total_cost
        
        # 굴절 횟수
        turn_count = allocation_result.turn_count
        
        # PRD 4.2 공사비 환산 점수 (cost_index) 계산
        cost_index = self._calculate_cost_index(
            poles_count,
            path_result.total_distance,
            turn_count
        )
        
        # 결과 설정
        result.cost_breakdown = breakdown
        result.detailed_breakdown = detailed
        result.total_cost = breakdown.total_cost
        result.total_distance = path_result.total_distance
        result.new_poles_count = poles_count
        result.start_pole_id = path_result.target_pole_id
        result.start_pole_coord = path_result.target_coord
        result.cost_index = cost_index
        result.turn_count = turn_count
        
        # 좌표 리스트 변환
        result.path_coordinates = [
            [coord[0], coord[1]] for coord in path_result.path_coords
        ]
        result.new_pole_coordinates = [
            pole.to_list() for pole in new_poles
        ]
        
        # Fast Track 비고
        if path_result.is_fast_track:
            result.remark = "FastTrack - 50m 이내 직접 연결"
        
        logger.info(
            f"공사비 계산: {path_result.target_pole_id} - "
            f"총 {breakdown.total_cost:,}원, cost_index={cost_index:,} "
            f"(전주 {poles_count}개, 거리 {path_result.total_distance:.1f}m, 굴절 {turn_count}회)"
        )
        
        return result
    
    def _calculate_basic(
        self,
        new_poles: List[NewPole],
        wire_length: float
    ) -> CostBreakdown:
        """기본 공사비 계산 (기존 방식)"""
        breakdown = CostBreakdown()
        poles_count = len(new_poles)
        
        # 1. 전선 비용
        breakdown.wire_cost = int(wire_length * self.wire_cost_per_meter)
        
        # 2. 전주 비용
        breakdown.pole_cost = poles_count * self.pole_cost
        
        # 3. 노무비
        breakdown.labor_cost = self.labor_base_cost
        if poles_count > 0:
            breakdown.labor_cost += int(poles_count * self.pole_cost * 0.1)
        
        # 4. 추가 비용 (분기점)
        junction_count = sum(1 for p in new_poles if p.is_junction)
        breakdown.extra_cost = junction_count * self.road_crossing_cost
        
        breakdown.calculate_total()
        return breakdown
    
    def _calculate_detailed(
        self,
        new_poles: List[NewPole],
        wire_length: float
    ) -> DetailedCostBreakdown:
        """상세 공사비 계산"""
        detailed = DetailedCostBreakdown()
        poles_count = len(new_poles)
        
        # ===== 재료비 =====
        material = detailed.material
        
        # 전주
        material.pole_count = poles_count
        material.pole_spec = self.pole_spec.value
        material.pole_unit_cost = POLE_COST_MAP.get(self.pole_spec, settings.COST_POLE)
        material.pole_cost = poles_count * material.pole_unit_cost
        
        # 전선
        material.wire_length = wire_length
        material.wire_spec = self.wire_spec.value
        material.wire_unit_cost = WIRE_COST_MAP.get(self.wire_spec, settings.COST_WIRE_LV)
        material.wire_cost = int(wire_length * material.wire_unit_cost)
        
        # 부자재 - 전주당 애자 3개, 완금 1개, 클램프 2개
        material.insulator_count = poles_count * 3
        material.insulator_cost = material.insulator_count * settings.COST_INSULATOR_PIN
        
        material.arm_tie_count = poles_count
        material.arm_tie_cost = material.arm_tie_count * settings.COST_ARM_TIE
        
        material.clamp_count = poles_count * 2
        material.clamp_cost = material.clamp_count * settings.COST_CLAMP
        
        # 접속자재 - 전주당 1개
        material.connector_count = max(1, poles_count)
        material.connector_cost = material.connector_count * settings.COST_CONNECTOR
        
        # ===== 인건비 =====
        labor = detailed.labor
        
        # 기본 노무비
        labor.base_labor_cost = settings.COST_LABOR_BASE
        
        # 전주 설치
        labor.pole_install_count = poles_count
        labor.pole_install_unit_cost = settings.COST_LABOR_POLE_INSTALL
        labor.pole_install_cost = poles_count * labor.pole_install_unit_cost
        
        # 전선 가선
        labor.wire_stretch_length = wire_length
        labor.wire_stretch_unit_cost = settings.COST_LABOR_WIRE_STRETCH
        labor.wire_stretch_cost = int(wire_length * labor.wire_stretch_unit_cost)
        
        # 애자 설치
        labor.insulator_install_count = material.insulator_count
        labor.insulator_install_unit_cost = settings.COST_LABOR_INSULATOR
        labor.insulator_install_cost = labor.insulator_install_count * labor.insulator_install_unit_cost
        
        # ===== 경비/이윤 =====
        detailed.overhead_rate = settings.OVERHEAD_RATE
        detailed.profit_rate = settings.PROFIT_RATE
        
        # ===== 추가 비용 =====
        junction_count = sum(1 for p in new_poles if p.is_junction)
        detailed.extra_cost = junction_count * self.road_crossing_cost
        if junction_count > 0:
            detailed.extra_detail = f"도로 횡단 {junction_count}회"
        
        # 전체 계산
        detailed.calculate_all()
        
        return detailed
    
    def _calculate_cost_index(
        self,
        poles_count: int,
        distance: float,
        turn_count: int
    ) -> int:
        """
        PRD 4.2 공사비 환산 점수(cost_index) 계산
        
        공식: Score = N_poles × W_pole + D × W_dist + N_turns × W_turn
        - W_pole = 10,000점 (전주 가중치) - 매우 높음
        - W_dist = 1점/m (거리 가중치)
        - W_turn = 50점 (굴절 가중치)
        
        낮은 점수일수록 우선순위가 높음
        예: 거리가 2m 더 멀더라도 전주를 1개 덜 심는 경로가 상위 랭크
        
        Args:
            poles_count: 신설 전주 개수
            distance: 총 거리 (m)
            turn_count: 굴절 횟수
        
        Returns:
            공사비 환산 점수
        """
        score = (
            poles_count * settings.SCORE_WEIGHT_POLE +
            int(distance * settings.SCORE_WEIGHT_DISTANCE) +
            turn_count * settings.SCORE_WEIGHT_TURN
        )
        return score
    
    def calculate_batch(
        self,
        allocation_results: List[AllocationResult]
    ) -> List[CostResult]:
        """
        여러 배치 결과에 대해 일괄 계산 및 순위 산정
        
        PRD 4.2에 따라 cost_index (공사비 환산 점수) 기준으로 정렬
        - 전주 개수가 최우선 (전주 1개 = 10,000점)
        - 같은 전주 수면 거리가 짧은 순
        
        Args:
            allocation_results: 배치 결과 리스트
        
        Returns:
            공사비 계산 결과 리스트 (cost_index 오름차순 정렬)
        """
        results = []
        
        for allocation in allocation_results:
            cost_result = self.calculate(allocation)
            results.append(cost_result)
        
        # PRD 4.2: cost_index 기준 정렬 (낮을수록 우선)
        results.sort(key=lambda r: r.cost_index)
        
        # 순위 설정
        for i, result in enumerate(results):
            result.rank = i + 1
        
        logger.info(f"총 {len(results)}개 경로 공사비 계산 완료 (cost_index 기준 정렬)")
        
        return results
    
    def estimate_cost(
        self,
        distance: float,
        poles_count: int = None
    ) -> int:
        """
        간단한 비용 추정 (상세 배치 없이)
        
        Args:
            distance: 거리 (m)
            poles_count: 전주 수 (None이면 거리 기반 추정)
        
        Returns:
            추정 비용 (원)
        """
        if poles_count is None:
            poles_count = max(1, int(distance / settings.POLE_INTERVAL))
        
        wire_cost = int(distance * self.wire_cost_per_meter)
        pole_cost = poles_count * self.pole_cost
        labor_cost = self.labor_base_cost + int(poles_count * self.pole_cost * 0.1)
        
        return wire_cost + pole_cost + labor_cost
    
    def get_spec_options(self) -> Dict[str, List[Dict[str, Any]]]:
        """사용 가능한 규격 옵션 반환"""
        return {
            "pole_specs": [
                {"code": spec.value, "cost": POLE_COST_MAP[spec]}
                for spec in PoleSpec if spec != PoleSpec.DEFAULT
            ],
            "wire_specs": [
                {"code": spec.value, "cost": WIRE_COST_MAP[spec]}
                for spec in WireSpec if spec != WireSpec.DEFAULT
            ]
        }