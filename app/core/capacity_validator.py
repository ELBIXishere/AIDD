"""
ELBIX AIDD 변압기 용량 검증 모듈
- 변압기 용량 적정성 검증
- 과부하 경고 및 용량 추천
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class TransformerCapacity(Enum):
    """변압기 표준 용량 (kVA)"""
    KVA_10 = 10
    KVA_20 = 20
    KVA_30 = 30
    KVA_50 = 50
    KVA_100 = 100
    KVA_200 = 200


# 변압기 용량별 단가 매핑
TRANSFORMER_COST = {
    TransformerCapacity.KVA_10: settings.COST_TRANSFORMER_10,
    TransformerCapacity.KVA_20: settings.COST_TRANSFORMER_20,
    TransformerCapacity.KVA_30: settings.COST_TRANSFORMER_30,
    TransformerCapacity.KVA_50: settings.COST_TRANSFORMER_50,
    TransformerCapacity.KVA_100: settings.COST_TRANSFORMER_100,
    TransformerCapacity.KVA_200: settings.COST_TRANSFORMER_200,
}


@dataclass
class TransformerInfo:
    """변압기 정보"""
    id: str                           # 변압기 ID
    pole_id: str                      # 연결 전주 ID
    capacity_kva: float               # 정격 용량 (kVA)
    current_load_kva: float = 0.0     # 현재 부하 (kVA)
    coord: Tuple[float, float] = (0, 0)  # 좌표
    
    @property
    def utilization_rate(self) -> float:
        """이용률 계산"""
        if self.capacity_kva <= 0:
            return 0.0
        return self.current_load_kva / self.capacity_kva
    
    @property
    def available_capacity(self) -> float:
        """가용 용량 (kVA)"""
        return max(0, self.capacity_kva - self.current_load_kva)


@dataclass
class CapacityValidationResult:
    """용량 검증 결과"""
    # 검증 대상
    transformer_id: str
    pole_id: str
    transformer_capacity_kva: float
    current_load_kva: float
    requested_load_kva: float
    
    # 계산 결과
    total_load_kva: float            # 신청 후 총 부하
    utilization_rate: float          # 이용률 (0.0 ~ 1.0)
    available_capacity: float        # 가용 용량
    
    # 검증 결과
    is_valid: bool                   # 용량 적합 여부
    is_warning: bool                 # 경고 수준 (75% 초과)
    message: str                     # 결과 메시지
    
    # 추천 정보
    recommended_capacity: Optional[float] = None  # 추천 용량
    upgrade_cost: Optional[int] = None           # 증설 비용


class CapacityValidator:
    """변압기 용량 검증기"""
    
    def __init__(
        self,
        overload_warning: float = None,
        overload_limit: float = None
    ):
        """
        Args:
            overload_warning: 경고 기준 이용률 (기본 0.75)
            overload_limit: 과부하 한계 이용률 (기본 1.0)
        """
        self.overload_warning = overload_warning or settings.TRANSFORMER_OVERLOAD_WARNING
        self.overload_limit = overload_limit or settings.TRANSFORMER_OVERLOAD_LIMIT
    
    def validate(
        self,
        transformer: TransformerInfo,
        requested_load_kw: float,
        power_factor: float = None
    ) -> CapacityValidationResult:
        """
        변압기 용량 검증
        
        Args:
            transformer: 변압기 정보
            requested_load_kw: 신청 부하 (kW)
            power_factor: 역률 (기본 0.9)
        
        Returns:
            용량 검증 결과
        """
        if power_factor is None:
            power_factor = settings.DEFAULT_POWER_FACTOR
        
        # kW → kVA 변환 (피상전력 = 유효전력 / 역률)
        requested_load_kva = requested_load_kw / power_factor
        
        # 총 부하 계산
        total_load_kva = transformer.current_load_kva + requested_load_kva
        
        # 이용률 계산
        utilization_rate = total_load_kva / transformer.capacity_kva if transformer.capacity_kva > 0 else float('inf')
        
        # 가용 용량
        available_capacity = max(0, transformer.capacity_kva - total_load_kva)
        
        # 검증
        is_valid = utilization_rate <= self.overload_limit
        is_warning = utilization_rate > self.overload_warning
        
        # 메시지 생성
        if not is_valid:
            message = (
                f"용량 초과! 변압기 {transformer.capacity_kva}kVA, "
                f"요청 후 총 부하 {total_load_kva:.1f}kVA (이용률 {utilization_rate*100:.1f}%)"
            )
        elif is_warning:
            message = (
                f"용량 경고: 변압기 {transformer.capacity_kva}kVA, "
                f"이용률 {utilization_rate*100:.1f}% (권장 {self.overload_warning*100:.0f}% 이하)"
            )
        else:
            message = (
                f"용량 적합: 변압기 {transformer.capacity_kva}kVA, "
                f"이용률 {utilization_rate*100:.1f}%, 가용 {available_capacity:.1f}kVA"
            )
        
        # 추천 용량 및 증설 비용
        recommended_capacity = None
        upgrade_cost = None
        
        if not is_valid or is_warning:
            recommended = self._recommend_capacity(total_load_kva)
            if recommended and recommended.value > transformer.capacity_kva:
                recommended_capacity = recommended.value
                upgrade_cost = TRANSFORMER_COST.get(recommended, 0)
        
        logger.info(
            f"변압기 용량 검증: {transformer.id} - {message}"
        )
        
        return CapacityValidationResult(
            transformer_id=transformer.id,
            pole_id=transformer.pole_id,
            transformer_capacity_kva=transformer.capacity_kva,
            current_load_kva=transformer.current_load_kva,
            requested_load_kva=requested_load_kva,
            total_load_kva=round(total_load_kva, 2),
            utilization_rate=round(utilization_rate, 4),
            available_capacity=round(available_capacity, 2),
            is_valid=is_valid,
            is_warning=is_warning,
            message=message,
            recommended_capacity=recommended_capacity,
            upgrade_cost=upgrade_cost
        )
    
    def _recommend_capacity(self, required_kva: float) -> Optional[TransformerCapacity]:
        """
        필요 용량에 맞는 변압기 추천
        
        Args:
            required_kva: 필요 용량 (kVA)
        
        Returns:
            추천 변압기 용량
        """
        # 권장 이용률 75%로 필요 용량 계산
        safe_capacity = required_kva / self.overload_warning
        
        # 적합한 용량 찾기
        for capacity in TransformerCapacity:
            if capacity.value >= safe_capacity:
                return capacity
        
        # 최대 용량 반환
        return TransformerCapacity.KVA_200
    
    def validate_batch(
        self,
        transformers: List[TransformerInfo],
        requested_load_kw: float,
        power_factor: float = None
    ) -> List[CapacityValidationResult]:
        """
        여러 변압기 일괄 검증
        
        Args:
            transformers: 변압기 목록
            requested_load_kw: 신청 부하 (kW)
            power_factor: 역률
        
        Returns:
            검증 결과 목록 (용량 적합 순 정렬)
        """
        results = []
        
        for transformer in transformers:
            result = self.validate(transformer, requested_load_kw, power_factor)
            results.append(result)
        
        # 정렬: 적합 > 경고 > 초과, 같은 수준이면 가용용량 큰 순
        results.sort(key=lambda r: (
            0 if r.is_valid and not r.is_warning else (1 if r.is_valid else 2),
            -r.available_capacity
        ))
        
        valid_count = sum(1 for r in results if r.is_valid)
        logger.info(f"총 {len(results)}개 변압기 검증 완료: {valid_count}개 적합")
        
        return results
    
    def find_suitable_transformer(
        self,
        transformers: List[TransformerInfo],
        requested_load_kw: float,
        power_factor: float = None
    ) -> Optional[Tuple[TransformerInfo, CapacityValidationResult]]:
        """
        적합한 변압기 찾기
        
        Args:
            transformers: 변압기 목록
            requested_load_kw: 신청 부하 (kW)
            power_factor: 역률
        
        Returns:
            (변압기 정보, 검증 결과) 또는 None
        """
        results = self.validate_batch(transformers, requested_load_kw, power_factor)
        
        # 적합하고 경고 없는 변압기 우선
        for i, result in enumerate(results):
            if result.is_valid and not result.is_warning:
                return transformers[i], result
        
        # 적합한 변압기 (경고 포함)
        for i, result in enumerate(results):
            if result.is_valid:
                return transformers[i], result
        
        return None
    
    def estimate_new_transformer(
        self,
        required_kw: float,
        power_factor: float = None
    ) -> Dict[str, Any]:
        """
        신규 변압기 설치 시 용량/비용 추정
        
        Args:
            required_kw: 필요 부하 (kW)
            power_factor: 역률
        
        Returns:
            추천 정보
        """
        if power_factor is None:
            power_factor = settings.DEFAULT_POWER_FACTOR
        
        required_kva = required_kw / power_factor
        recommended = self._recommend_capacity(required_kva)
        
        if recommended:
            return {
                "required_kva": round(required_kva, 2),
                "recommended_capacity_kva": recommended.value,
                "estimated_cost": TRANSFORMER_COST.get(recommended, 0),
                "utilization_rate": round(required_kva / recommended.value, 4),
                "message": f"권장 변압기: {recommended.value}kVA (이용률 {required_kva/recommended.value*100:.1f}%)"
            }
        else:
            return {
                "required_kva": round(required_kva, 2),
                "recommended_capacity_kva": None,
                "estimated_cost": 0,
                "message": "적합한 표준 변압기 용량 없음"
            }
    
    def get_capacity_options(self) -> List[Dict[str, Any]]:
        """사용 가능한 변압기 용량 옵션 반환"""
        return [
            {
                "capacity_kva": cap.value,
                "cost": TRANSFORMER_COST.get(cap, 0),
                "max_load_kw_at_90pf": round(cap.value * settings.DEFAULT_POWER_FACTOR, 1)
            }
            for cap in TransformerCapacity
        ]
