"""
ELBIX AIDD 후보 전주 선별기
- Phase Matching: 3상/단상 매칭
- Fast Track: 50m 이내 직접 연결 체크
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
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
    fast_track_target: Optional[TargetPole] = None  # Fast Track 대상
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
        # 전주 ID → 연결된 전선 리스트
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
        """
        전주의 전선 연결 타입 분석
        
        Args:
            pole_id: 전주 ID
        
        Returns:
            {
                'has_lv': 저압선 연결 여부,
                'has_hv': 고압선 연결 여부,
                'has_hv_3phase': 고압 3상선 연결 여부,
                'lv_only': 저압선만 연결 여부
            }
        """
        result = {
            'has_lv': False,
            'has_hv': False,
            'has_hv_3phase': False,
            'lv_only': False
        }
        
        if pole_id not in self.pole_to_lines:
            return result
        
        lines = self.pole_to_lines[pole_id]
        
        for line in lines:
            if line.is_high_voltage:
                result['has_hv'] = True
                if line.phase_code == settings.PHASE_THREE:
                    result['has_hv_3phase'] = True
            else:
                result['has_lv'] = True
        
        # 저압선만 연결된 경우
        result['lv_only'] = result['has_lv'] and not result['has_hv']
        
        return result
    
    def select(
        self,
        consumer_coord: Tuple[float, float],
        phase_code: str
    ) -> SelectionResult:
        """
        후보 전주 선별
        
        Args:
            consumer_coord: 수용가 좌표 (x, y)
            phase_code: 신청 상 코드 ("1": 단상, "3": 3상)
        
        Returns:
            선별 결과
        """
        result = SelectionResult(
            targets=[],
            consumer_coord=consumer_coord,
            phase_code=phase_code
        )
        
        # Step 1: Phase Matching - 상 조건에 맞는 전주 필터링
        matched_poles = self._phase_matching(phase_code)
        
        if not matched_poles:
            result.message = f"상 조건({phase_code})에 맞는 전주가 없습니다."
            logger.warning(result.message)
            return result
        
        logger.info(f"Phase Matching 결과: {len(matched_poles)}개 전주")
        
        # Step 2: 거리 계산 및 400m 이내 필터링
        target_poles = []
        for pole in matched_poles:
            distance = calculate_distance(
                consumer_coord[0], consumer_coord[1],
                pole.coord[0], pole.coord[1]
            )
            
            # 최대 거리 제한 (400m)
            if distance > settings.MAX_DISTANCE_LIMIT:
                continue
            
            target = TargetPole(
                pole=pole,
                distance_to_consumer=distance
            )
            target_poles.append(target)
        
        if not target_poles:
            result.message = f"400m 이내에 적합한 전주가 없습니다."
            logger.warning(result.message)
            return result
        
        logger.info(f"거리 필터링 결과: {len(target_poles)}개 전주")
        
        # Step 3: Fast Track 체크 (50m 이내)
        for target in target_poles:
            if target.distance_to_consumer <= settings.FAST_TRACK_DISTANCE:
                # 장애물 체크
                has_obstacle = self._check_obstacle(
                    consumer_coord, target.coord
                )
                target.has_obstacle = has_obstacle
                
                if not has_obstacle:
                    target.is_fast_track = True
                    target.priority = 0  # 최우선
        
        # Step 4: 우선순위 설정
        for target in target_poles:
            if not target.is_fast_track:
                # 기본 우선순위: 거리 기반
                target.priority = int(target.distance_to_consumer)
                
                # 전선 연결 타입 분석
                conn = self._analyze_pole_connections(target.pole.id)
                
                if phase_code == settings.PHASE_SINGLE:
                    # [단상 설계] 저압선 연결 전주 우선
                    # - 단상 수용가는 저압선(LV, 220V/380V)에 연결이 표준
                    # - 고압선만 연결된 전주는 변압기 추가 설치 필요 (후순위)
                    if conn['has_lv']:
                        target.priority -= 100  # 저압선 연결 → 최우선
                    elif conn['has_hv'] and not conn['has_lv']:
                        target.priority += 50   # 고압선만 연결 → 패널티
                else:
                    # [3상 설계] 고압 3상선 연결 전주 우선
                    # - 3상 수용가는 반드시 고압(22.9kV) 3상 선로에 연결 필요
                    if conn['has_hv_3phase']:
                        target.priority -= 100  # 3상 고압선 연결 → 최우선
                    elif conn['has_hv']:
                        target.priority -= 50   # 고압선 연결 → 차선
                    
                    # 추가: 전주 자체가 3상인 경우 보너스
                    if target.pole.is_three_phase:
                        target.priority -= 20
        
        # Step 5: 정렬 (우선순위 오름차순)
        target_poles.sort(key=lambda t: (t.priority, t.distance_to_consumer))
        
        # Fast Track 대상 설정
        fast_track_targets = [t for t in target_poles if t.is_fast_track]
        if fast_track_targets:
            result.fast_track_target = fast_track_targets[0]
            result.message = f"Fast Track 가능: {result.fast_track_target.id} ({result.fast_track_target.distance_to_consumer:.1f}m)"
            logger.info(result.message)
        
        result.targets = target_poles
        result.message = f"{len(target_poles)}개 후보 전주 선별 완료"
        
        return result
    
    def _phase_matching(self, phase_code: str) -> List[Pole]:
        """
        Phase Matching: 상 조건에 맞는 전주 필터링
        
        [배전설계기준]
        - 3상 요청: 반드시 고압(22.9kV) 3상 선로에 연결된 전주만 허용
        - 단상 요청: 고압 또는 저압 선로에 연결된 전주 허용
        
        Args:
            phase_code: 신청 상 코드 ("1": 단상, "3": 3상)
        
        Returns:
            조건에 맞는 전주 리스트
        """
        if phase_code == settings.PHASE_THREE:
            # 3상 요청: 고압 3상 선로가 연결된 전주만 (필수 조건)
            logger.info("3상 설계: 고압 3상 선로 연결 전주만 선별")
            return self._get_three_phase_connected_poles()
        else:
            # 단상 요청: 모든 전선(고압/저압)이 연결된 전주 허용
            logger.info("단상 설계: 전선 연결 전주 선별 (고압/저압 모두 허용)")
            return self._get_single_phase_connectable_poles()
    
    def _get_single_phase_connectable_poles(self) -> List[Pole]:
        """
        단상 공급 가능 전주 반환
        
        [배전설계기준]
        - 단상은 고압 또는 저압 선로 모두에서 공급 가능
        - 전선이 연결된 전주만 후보로 선정 (전선 없는 전주 제외)
        - 저압선 연결 전주 우선, 고압선 연결 전주도 포함
        """
        # 전선에 연결된 모든 전주 ID 수집
        connected_pole_ids = set()
        lv_connected_pole_ids = set()  # 저압선 연결
        hv_connected_pole_ids = set()  # 고압선 연결
        
        for line in self.lines:
            pole_ids = []
            if line.start_pole_id:
                pole_ids.append(line.start_pole_id)
            if line.end_pole_id:
                pole_ids.append(line.end_pole_id)
            
            for pole_id in pole_ids:
                connected_pole_ids.add(pole_id)
                if line.is_high_voltage:
                    hv_connected_pole_ids.add(pole_id)
                else:
                    lv_connected_pole_ids.add(pole_id)
        
        result_poles = []
        result_pole_ids = set()
        
        for pole in self.poles:
            # 전선에 연결되지 않은 전주는 제외
            if pole.id not in connected_pole_ids:
                continue
            
            if pole.id in result_pole_ids:
                continue
            
            # 저압선 연결 전주 우선 (단상 공급에 적합)
            if pole.id in lv_connected_pole_ids:
                result_poles.insert(0, pole)  # 앞에 추가
            else:
                result_poles.append(pole)
            
            result_pole_ids.add(pole.id)
        
        logger.info(f"단상 후보 전주 선별: 총 {len(result_poles)}개")
        logger.debug(f"  - 저압선 연결: {len(lv_connected_pole_ids)}개")
        logger.debug(f"  - 고압선 연결: {len(hv_connected_pole_ids)}개")
        
        return result_poles
    
    def _get_three_phase_connected_poles(self) -> List[Pole]:
        """
        3상 공급 가능 전주 반환
        
        [중요] 3상 설계 규칙 (배전설계기준):
        - 3상 수용가는 반드시 고압(22.9kV) 3상 선로에 연결해야 함
        - 저압선만 연결된 전주에는 연결 불가
        - 고압 3상 선로가 연결된 전주만 후보로 선정
        """
        logger.info(f"3상 후보 전주 선별 시작: 전주 {len(self.poles)}개, 전선 {len(self.lines)}개")
        
        # 전선 타입 디버깅
        hv_count = sum(1 for l in self.lines if l.is_high_voltage)
        three_phase_count = sum(1 for l in self.lines if l.phase_code == settings.PHASE_THREE)
        logger.info(f"  전선 분석: 고압선 {hv_count}개, 3상선 {three_phase_count}개")
        
        # 1단계: 3상 고압선에 연결된 전주 ID 수집 (필수 조건)
        three_phase_hv_pole_ids = set()
        for line in self.lines:
            # 반드시 고압선(HV)이면서 3상인 경우만
            if line.is_high_voltage and line.phase_code == settings.PHASE_THREE:
                if line.start_pole_id:
                    three_phase_hv_pole_ids.add(line.start_pole_id)
                if line.end_pole_id:
                    three_phase_hv_pole_ids.add(line.end_pole_id)
        
        # 2단계: 고압선에 연결된 전주 ID 수집 (3상이 아니더라도 고압선 연결)
        # 일부 데이터에서 phase_code가 없을 수 있으므로 고압선 연결 전주도 포함
        hv_connected_pole_ids = set()
        for line in self.lines:
            if line.is_high_voltage:
                if line.start_pole_id:
                    hv_connected_pole_ids.add(line.start_pole_id)
                if line.end_pole_id:
                    hv_connected_pole_ids.add(line.end_pole_id)
        
        # 3단계: 저압선만 연결된 전주 ID 수집 (제외 대상)
        lv_only_pole_ids = set()
        for line in self.lines:
            if not line.is_high_voltage:  # 저압선
                if line.start_pole_id:
                    lv_only_pole_ids.add(line.start_pole_id)
                if line.end_pole_id:
                    lv_only_pole_ids.add(line.end_pole_id)
        
        # 고압선도 연결된 전주는 저압전용에서 제외
        lv_only_pole_ids = lv_only_pole_ids - hv_connected_pole_ids
        
        result_poles = []
        result_pole_ids = set()
        
        for pole in self.poles:
            # [필수] 고압선에 연결된 전주만 후보로 선정
            if pole.id not in hv_connected_pole_ids:
                continue
            
            # [제외] 저압선만 연결된 전주는 제외
            if pole.id in lv_only_pole_ids:
                continue
            
            # 우선순위 부여
            # 우선순위 1: 3상 고압선에 직접 연결된 전주 (최우선)
            if pole.id in three_phase_hv_pole_ids:
                if pole.id not in result_pole_ids:
                    result_poles.insert(0, pole)  # 앞에 추가
                    result_pole_ids.add(pole.id)
                continue
            
            # 우선순위 2: 고압선에 연결된 전주 (3상 데이터 없는 경우)
            if pole.id in hv_connected_pole_ids:
                if pole.id not in result_pole_ids:
                    result_poles.append(pole)
                    result_pole_ids.add(pole.id)
        
        logger.info(f"3상 후보 전주 선별: 총 {len(result_poles)}개")
        logger.debug(f"  - 3상 고압선 연결: {len(three_phase_hv_pole_ids)}개")
        logger.debug(f"  - 고압선 연결: {len(hv_connected_pole_ids)}개")
        logger.debug(f"  - 저압선만 연결 (제외됨): {len(lv_only_pole_ids)}개")
        
        return result_poles
    
    def _check_obstacle(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float]
    ) -> bool:
        """
        두 점 사이에 장애물(건물)이 있는지 확인
        
        Args:
            start: 시작점 (수용가)
            end: 끝점 (전주)
        
        Returns:
            장애물 있으면 True
        """
        if not self.buildings:
            return False
        
        # 두 점을 연결하는 선
        line = LineString([start, end])
        
        # 건물과 교차 여부 확인
        for building in self.buildings:
            if line.intersects(building.geometry):
                # 접촉만 하는 경우는 제외 (교차만 확인)
                if not line.touches(building.geometry):
                    return True
        
        return False
    
    def get_nearest_target(
        self,
        consumer_coord: Tuple[float, float],
        phase_code: str
    ) -> Optional[TargetPole]:
        """
        가장 가까운 후보 전주 반환
        """
        result = self.select(consumer_coord, phase_code)
        return result.targets[0] if result.targets else None
    
    def get_fast_track_target(
        self,
        consumer_coord: Tuple[float, float],
        phase_code: str
    ) -> Optional[TargetPole]:
        """
        Fast Track 가능한 전주 반환 (없으면 None)
        """
        result = self.select(consumer_coord, phase_code)
        return result.fast_track_target
