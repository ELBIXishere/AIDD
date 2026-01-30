"""
ELBIX AIDD 후보 전주 선별기
- Phase Matching: 3상/단상 매칭
- Fast Track: 40m 이내 직접 연결 체크
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from shapely.geometry import Point, LineString

from app.config import settings
from app.core.preprocessor import Pole, Line, Building, ProcessedData
from app.utils.coordinate import calculate_distance
import logging

logger = logging.getLogger(__name__)


@dataclass
class TargetPole:
    """후보 전주 (Target Pole)"""
    pole: Pole                          # 원본 전주 데이터
    distance_to_consumer: float         # 수용가까지 직선 거리 (m)
    is_fast_track: bool = False         # Fast Track 가능 여부
    has_obstacle: bool = False          # 장애물 존재 여부
    priority: int = 0                   # 우선순위 (낮을수록 우선)
    
    @property
    def id(self) -> str:
        return self.pole.id
    
    @property
    def coord(self) -> Tuple[float, float]:
        return self.pole.coord


@dataclass
class SelectionResult:
    """선별 결과"""
    targets: List[TargetPole]           # 후보 전주 목록 (우선순위 순)
    fast_track_targets: List[TargetPole] = field(default_factory=list) # [MOD] 다중 Fast Track 후보
    consumer_coord: Tuple[float, float] = (0, 0)    # 수용가 좌표
    phase_code: str = ""                # 요청 상 코드
    message: str = ""                   # 결과 메시지


class TargetSelector:
    """후보 전주 선별기"""
    
    def __init__(self, processed_data: ProcessedData):
        """
        Args:
            processed_data: 전처리된 데이터
        """
        self.data = processed_data
        self.poles = processed_data.poles
        self.lines = processed_data.lines
        self.buildings = processed_data.buildings
        
        # 전주-전선 연결 관계 구축
        self._build_pole_line_map()
    
    def _build_pole_line_map(self):
        """전주-전선 연결 관계 맵 생성"""
        self.pole_to_lines: Dict[str, List[Line]] = {}
        for line in self.lines:
            if line.start_pole_id:
                if line.start_pole_id not in self.pole_to_lines:
                    self.pole_to_lines[line.start_pole_id] = []
                self.pole_to_lines[line.start_pole_id].append(line)
            if line.end_pole_id:
                if line.end_pole_id not in self.pole_to_lines:
                    self.pole_to_lines[line.end_pole_id] = []
                self.pole_to_lines[line.end_pole_id].append(line)
    
    def _analyze_pole_connections(self, pole_id: str) -> Dict[str, bool]:
        """전주의 전선 연결 타입 분석"""
        result = {'has_lv': False, 'has_hv': False, 'has_hv_3phase': False}
        if pole_id not in self.pole_to_lines:
            return result
        
        for line in self.pole_to_lines[pole_id]:
            if line.line_type == "HV":
                result['has_hv'] = True
                if line.phase_code == "3":
                    result['has_hv_3phase'] = True
            else:
                result['has_lv'] = True
        return result
    
    def select(self, consumer_coord: Tuple[float, float], phase_code: str) -> SelectionResult:
        """후보 전주 선별 메인 로직 (순정 상태)"""
        result = SelectionResult(targets=[], consumer_coord=consumer_coord, phase_code=phase_code)
        
        # 1. 상 매칭 (필터링)
        matched_poles = self._phase_matching(phase_code)
        if not matched_poles:
            return result
        
        # 2. 거리 필터링 (400m)
        target_poles = []
        for pole in matched_poles:
            dist = calculate_distance(consumer_coord[0], consumer_coord[1], pole.coord[0], pole.coord[1])
            if dist <= settings.MAX_DISTANCE_LIMIT:
                target_poles.append(TargetPole(pole=pole, distance_to_consumer=dist))
        
        # 3. 우선순위 및 Fast Track 체크 (자연스러운 가중치)
        for target in target_poles:
            # 기본 점수 = 직선 거리
            score = target.distance_to_consumer
            
            # 공학적 보너스: 변압기나 저압선(LV)이 있으면 비용 절감 효과 반영 (약 50~100m 보너스)
            conn = self._analyze_pole_connections(target.pole.id)
            
            if phase_code == "1":
                if target.pole.has_transformer:
                    score -= 100.0  # 변압기가 바로 있으면 최우선 (변압기 신설 필요 없음)
                elif conn['has_lv']:
                    score -= 50.0   # 저압선이라도 있으면 우선
            elif phase_code == "3":
                if target.pole.has_transformer and target.pole.is_three_phase:
                    score -= 150.0  # 3상 변압기가 있으면 최우선
                elif conn['has_hv_3phase']:
                    score -= 100.0  # 고압 3상이라도 있으면 우선
            
            target.priority = int(score)
            
            # Fast Track 체크 (40m 이내, 장애물 없을 시)
            if target.distance_to_consumer <= settings.FAST_TRACK_DISTANCE:
                if not self._check_obstacle(consumer_coord, target.coord):
                    target.is_fast_track = True

        # 4. 최종 정렬
        target_poles.sort(key=lambda t: (t.priority, t.distance_to_consumer))
        
        result.targets = target_poles
        if target_poles and target_poles[0].is_fast_track:
            result.fast_track_target = target_poles[0]
            
        return result

    def _phase_matching(self, phase_code: str) -> List[Pole]:
        if phase_code == "3":
            return self._get_three_phase_connected_poles()
        else:
            return self._get_single_phase_connectable_poles()

    def _get_single_phase_connectable_poles(self) -> List[Pole]:
        connected_pole_ids = {line.start_pole_id for line in self.lines if line.start_pole_id}
        connected_pole_ids.update({line.end_pole_id for line in self.lines if line.end_pole_id})
        return [p for p in self.poles if p.id in connected_pole_ids]

    def _get_three_phase_connected_poles(self) -> List[Pole]:
        hv_connected_ids = set()
        for line in self.lines:
            if line.line_type == "HV":
                if line.start_pole_id: hv_connected_ids.add(line.start_pole_id)
                if line.end_pole_id: hv_connected_ids.add(line.end_pole_id)
        return [p for p in self.poles if p.id in hv_connected_ids]

    def _check_obstacle(self, start: Tuple[float, float], end: Tuple[float, float]) -> bool:
        if not self.buildings: return False
        line = LineString([start, end])
        for building in self.buildings:
            if line.intersects(building.geometry) and not line.touches(building.geometry):
                return True
        return False
