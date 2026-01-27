"""
ELBIX AIDD 전압 강하 계산 모듈
- 단상/3상 전압 강하율 계산
- 허용 전압 강하 검증
"""

import math
from typing import Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class WireType(Enum):
    """전선 종류"""
    ACSR_58 = "ACSR_58"
    ACSR_95 = "ACSR_95"
    ACSR_160 = "ACSR_160"
    OW_22 = "OW_22"
    OW_38 = "OW_38"


# 전선 저항/리액턴스 매핑 (Ω/km)
WIRE_RESISTANCE = {
    WireType.ACSR_58: settings.WIRE_RESISTANCE_ACSR_58,
    WireType.ACSR_95: settings.WIRE_RESISTANCE_ACSR_95,
    WireType.ACSR_160: settings.WIRE_RESISTANCE_ACSR_160,
    WireType.OW_22: settings.WIRE_RESISTANCE_OW_22,
    WireType.OW_38: settings.WIRE_RESISTANCE_OW_38,
}

WIRE_REACTANCE = {
    WireType.ACSR_58: settings.WIRE_REACTANCE_ACSR_58,
    WireType.ACSR_95: settings.WIRE_REACTANCE_ACSR_95,
    WireType.ACSR_160: settings.WIRE_REACTANCE_ACSR_160,
    WireType.OW_22: settings.WIRE_REACTANCE_OW_22,
    WireType.OW_38: settings.WIRE_REACTANCE_OW_38,
}


@dataclass
class VoltageDropResult:
    """전압 강하 계산 결과"""
    # 입력 값
    distance: float              # 거리 (m)
    load_kw: float               # 부하 (kW)
    phase_type: str              # 상 ("1" 또는 "3")
    wire_type: str               # 전선 종류
    
    # 계산 값
    load_current: float          # 부하 전류 (A)
    voltage_drop_v: float        # 전압 강하 (V)
    voltage_drop_percent: float  # 전압 강하율 (%)
    
    # 검증 결과
    is_acceptable: bool          # 허용 범위 내 여부
    limit_percent: float         # 허용 전압 강하 한계 (%)
    message: str                 # 결과 메시지


class VoltageCalculator:
    """전압 강하 계산기"""
    
    def __init__(
        self,
        power_factor: float = None,
        voltage_lv: int = None,
        voltage_lv_3p: int = None,
        voltage_hv: int = None
    ):
        """
        Args:
            power_factor: 역률 (기본 0.9)
            voltage_lv: 저압 단상 전압 (V)
            voltage_lv_3p: 저압 3상 전압 (V)
            voltage_hv: 고압 전압 (V)
        """
        self.power_factor = power_factor or settings.DEFAULT_POWER_FACTOR
        self.voltage_lv = voltage_lv or settings.NOMINAL_VOLTAGE_LV
        self.voltage_lv_3p = voltage_lv_3p or settings.NOMINAL_VOLTAGE_LV_3P
        self.voltage_hv = voltage_hv or settings.NOMINAL_VOLTAGE_HV
    
    def calculate(
        self,
        distance: float,
        load_kw: float,
        phase_type: str = "1",
        wire_type: WireType = WireType.OW_22,
        is_high_voltage: bool = False
    ) -> VoltageDropResult:
        """
        전압 강하 계산
        
        단상: e = (2 × I × (R×cosθ + X×sinθ) × L) / V × 100 (%)
        3상: e = (√3 × I × (R×cosθ + X×sinθ) × L) / V × 100 (%)
        
        Args:
            distance: 거리 (m)
            load_kw: 부하 용량 (kW)
            phase_type: 상 타입 ("1": 단상, "3": 3상)
            wire_type: 전선 종류
            is_high_voltage: 고압 여부
        
        Returns:
            전압 강하 계산 결과
        """
        # 전압 결정
        if is_high_voltage:
            nominal_voltage = self.voltage_hv
            limit_percent = settings.VOLTAGE_DROP_LIMIT_HV
        elif phase_type == "3":
            nominal_voltage = self.voltage_lv_3p
            limit_percent = settings.VOLTAGE_DROP_LIMIT_LV
        else:
            nominal_voltage = self.voltage_lv
            limit_percent = settings.VOLTAGE_DROP_LIMIT_LV
        
        # 부하 전류 계산 (I = P / (V × cosθ × √3) for 3상, I = P / (V × cosθ) for 단상)
        if phase_type == "3":
            load_current = (load_kw * 1000) / (math.sqrt(3) * nominal_voltage * self.power_factor)
        else:
            load_current = (load_kw * 1000) / (nominal_voltage * self.power_factor)
        
        # 저항/리액턴스 (Ω/km)
        resistance = WIRE_RESISTANCE.get(wire_type, settings.WIRE_RESISTANCE_OW_22)
        reactance = WIRE_REACTANCE.get(wire_type, settings.WIRE_REACTANCE_OW_22)
        
        # 거리 (km로 변환)
        distance_km = distance / 1000.0
        
        # 역률 관련 계수
        cos_theta = self.power_factor
        sin_theta = math.sqrt(1 - cos_theta ** 2)
        
        # 임피던스 성분
        z_component = resistance * cos_theta + reactance * sin_theta
        
        # 전압 강하 계산 (V)
        if phase_type == "3":
            voltage_drop_v = math.sqrt(3) * load_current * z_component * distance_km
        else:
            voltage_drop_v = 2 * load_current * z_component * distance_km
        
        # 전압 강하율 (%)
        voltage_drop_percent = (voltage_drop_v / nominal_voltage) * 100
        
        # 허용 범위 확인
        is_acceptable = voltage_drop_percent <= limit_percent
        
        # 결과 메시지
        if is_acceptable:
            message = f"전압 강하 {voltage_drop_percent:.2f}% - 허용 범위 내 (한계: {limit_percent}%)"
        else:
            message = f"전압 강하 {voltage_drop_percent:.2f}% - 한계 초과! (한계: {limit_percent}%)"
        
        logger.info(
            f"전압 강하 계산: {distance:.1f}m, {load_kw}kW, {phase_type}상, "
            f"{wire_type.value} → {voltage_drop_percent:.2f}% ({message})"
        )
        
        return VoltageDropResult(
            distance=distance,
            load_kw=load_kw,
            phase_type=phase_type,
            wire_type=wire_type.value,
            load_current=round(load_current, 2),
            voltage_drop_v=round(voltage_drop_v, 2),
            voltage_drop_percent=round(voltage_drop_percent, 2),
            is_acceptable=is_acceptable,
            limit_percent=limit_percent,
            message=message
        )
    
    def calculate_max_distance(
        self,
        load_kw: float,
        max_drop_percent: float = None,
        phase_type: str = "1",
        wire_type: WireType = WireType.OW_22,
        is_high_voltage: bool = False
    ) -> float:
        """
        허용 전압 강하 내 최대 거리 계산
        
        Args:
            load_kw: 부하 용량 (kW)
            max_drop_percent: 최대 허용 전압 강하율 (%)
            phase_type: 상 타입
            wire_type: 전선 종류
            is_high_voltage: 고압 여부
        
        Returns:
            최대 허용 거리 (m)
        """
        # 허용 전압 강하 결정
        if max_drop_percent is None:
            if is_high_voltage:
                max_drop_percent = settings.VOLTAGE_DROP_LIMIT_HV
            else:
                max_drop_percent = settings.VOLTAGE_DROP_LIMIT_LV
        
        # 전압 결정
        if is_high_voltage:
            nominal_voltage = self.voltage_hv
        elif phase_type == "3":
            nominal_voltage = self.voltage_lv_3p
        else:
            nominal_voltage = self.voltage_lv
        
        # 부하 전류 계산
        if phase_type == "3":
            load_current = (load_kw * 1000) / (math.sqrt(3) * nominal_voltage * self.power_factor)
        else:
            load_current = (load_kw * 1000) / (nominal_voltage * self.power_factor)
        
        # 저항/리액턴스
        resistance = WIRE_RESISTANCE.get(wire_type, settings.WIRE_RESISTANCE_OW_22)
        reactance = WIRE_REACTANCE.get(wire_type, settings.WIRE_REACTANCE_OW_22)
        
        cos_theta = self.power_factor
        sin_theta = math.sqrt(1 - cos_theta ** 2)
        z_component = resistance * cos_theta + reactance * sin_theta
        
        # 최대 허용 전압 강하 (V)
        max_drop_v = (max_drop_percent / 100) * nominal_voltage
        
        # 최대 거리 계산 (km)
        if phase_type == "3":
            max_distance_km = max_drop_v / (math.sqrt(3) * load_current * z_component)
        else:
            max_distance_km = max_drop_v / (2 * load_current * z_component)
        
        # m로 변환
        max_distance_m = max_distance_km * 1000
        
        logger.info(
            f"최대 허용 거리: {load_kw}kW, {phase_type}상, {wire_type.value} → {max_distance_m:.1f}m"
        )
        
        return round(max_distance_m, 1)
    
    def recommend_wire(
        self,
        distance: float,
        load_kw: float,
        phase_type: str = "1"
    ) -> Tuple[WireType, VoltageDropResult]:
        """
        적합한 전선 규격 추천
        
        Args:
            distance: 거리 (m)
            load_kw: 부하 용량 (kW)
            phase_type: 상 타입
        
        Returns:
            (추천 전선 종류, 전압 강하 결과)
        """
        # 규격 순서 (작은 것부터)
        wire_order = [
            WireType.OW_22,
            WireType.OW_38,
            WireType.ACSR_58,
            WireType.ACSR_95,
            WireType.ACSR_160,
        ]
        
        for wire_type in wire_order:
            result = self.calculate(distance, load_kw, phase_type, wire_type)
            if result.is_acceptable:
                logger.info(f"전선 추천: {wire_type.value} (전압 강하 {result.voltage_drop_percent}%)")
                return wire_type, result
        
        # 모든 규격에서 초과 시 최대 규격 반환
        largest_wire = WireType.ACSR_160
        result = self.calculate(distance, load_kw, phase_type, largest_wire)
        logger.warning(f"모든 전선 규격에서 전압 강하 초과: {largest_wire.value} 사용 권장")
        return largest_wire, result
