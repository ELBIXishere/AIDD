"""
ELBIX AIDD 신설 전주 배치 모듈
- 수용가 위치에 첫 전주 필수 배치
- 이후 40m 간격으로 전주 배치
- 분기점 필수 배치
- 기설전주 근처(15m 이내)에는 신설 전주 배치 안함
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from shapely.geometry import Point, LineString
import logging
import math

from app.config import settings
from app.core.pathfinder import PathResult
from app.utils.coordinate import calculate_distance
from app.utils.geometry import interpolate_points_on_line, calculate_angle

logger = logging.getLogger(__name__)


@dataclass
class NewPole:
    """신설 전주"""
    id: str
    coord: Tuple[float, float]
    sequence: int              # 순번 (수용가에서부터)
    distance_from_consumer: float  # 수용가로부터의 누적 거리
    is_junction: bool = False  # 분기점 여부
    
    def to_list(self) -> List[float]:
        """좌표를 리스트로 반환"""
        return [self.coord[0], self.coord[1]]


@dataclass
class AllocationResult:
    """배치 결과"""
    path_result: PathResult             # 원본 경로 결과
    new_poles: List[NewPole] = field(default_factory=list)
    total_wire_length: float = 0.0      # 전선 총 길이
    turn_count: int = 0                 # 굴절 횟수 (PRD 4.2 Scoring용)
    message: str = ""


class PoleAllocator:
    """신설 전주 배치기"""
    
    # 기설전주와의 최소 거리 (이 거리 이내에는 신설전주 배치 안함)
    # 이유: 접속 구간/중복 시설 방지/작업 여유 등. 상세·근거는 docs/전주배치_규칙.md §2.1 참고.
    MIN_DISTANCE_TO_EXISTING_POLE = 15.0
    
    def __init__(
        self,
        pole_interval: float = None,
        first_pole_max_distance: float = None
    ):
        """
        Args:
            pole_interval: 전주 간격 (기본: 40m)
            first_pole_max_distance: 첫 전주 최대 거리 (기본: 30m)
        """
        self.pole_interval = pole_interval or settings.POLE_INTERVAL
        self.first_pole_max_distance = first_pole_max_distance or settings.FIRST_POLE_MAX_DISTANCE
        self.pole_counter = 0
    
    def allocate(self, path_result: PathResult) -> AllocationResult:
        """
        경로 위에 신설 전주 배치
        
        Args:
            path_result: 경로 탐색 결과
        
        Returns:
            배치 결과
        """
        result = AllocationResult(path_result=path_result)
        
        if not path_result.is_reachable:
            result.message = "도달 불가능한 경로"
            return result
        
        path_coords = path_result.path_coords
        
        if len(path_coords) < 2:
            result.message = "경로 좌표가 부족합니다"
            return result
        
        # Fast Track(직접 연결)인 경우에도 수용가 위치에 신설 전주 1개는 필수
        if path_result.is_fast_track:
            path_line = LineString(path_coords)
            consumer_coord = path_coords[0]
            self.pole_counter += 1
            pole_at_consumer = NewPole(
                id=f"NEW_POLE_{self.pole_counter}",
                coord=tuple(consumer_coord),
                sequence=1,
                distance_from_consumer=0.0,
                is_junction=False
            )
            result.new_poles = [pole_at_consumer]
            result.total_wire_length = path_result.total_distance
            result.message = "Fast Track - 수용가 위치 신설 전주 1개"
            return result
        
        # 경로를 LineString으로 변환
        path_line = LineString(path_coords)
        total_length = path_line.length
        
        # 기설전주까지의 유효 거리 (기설전주 15m 전까지만 배치)
        effective_length = total_length - self.MIN_DISTANCE_TO_EXISTING_POLE
        
        # 전주 배치 위치 계산
        pole_positions = self._calculate_pole_positions(
            path_coords,
            total_length
        )
        
        # 분기점 (꺾이는 지점) 찾기
        junction_positions = self._find_junctions(path_coords)
        
        # 분기점도 effective_length를 초과하지 않도록 필터링
        # 기설전주 15m 이내에는 신설전주 배치 안함
        filtered_junction_positions = [
            (pos, is_junction) for pos, is_junction in junction_positions
            if pos <= effective_length
        ]
        
        # 디버깅 로그
        if junction_positions:
            logger.info(f"분기점 발견: 총 {len(junction_positions)}개, "
                       f"필터링 후 {len(filtered_junction_positions)}개 "
                       f"(effective_length: {effective_length:.1f}m)")
            for pos, _ in filtered_junction_positions:
                logger.debug(f"  - 분기점 위치: {pos:.1f}m")
        
        # 굴절 횟수 계산 (PRD 4.2 Scoring용) - 필터링 전 원본 사용
        turn_count = len(junction_positions)
        
        # 위치 병합 및 정렬
        all_positions = self._merge_positions(pole_positions, filtered_junction_positions)
        
        # 디버깅 로그
        logger.info(f"전주 배치: 일반 {len(pole_positions)}개, "
                   f"분기점 {len(filtered_junction_positions)}개, "
                   f"병합 후 총 {len(all_positions)}개")
        
        # NewPole 객체 생성
        new_poles = []
        cumulative_distance = 0.0
        prev_coord = path_coords[0]  # 수용가 좌표
        
        for i, (pos, is_junction) in enumerate(all_positions):
            # 경로 위의 좌표 계산
            point = path_line.interpolate(pos)
            coord = (point.x, point.y)
            
            # 거리 계산
            distance = calculate_distance(
                prev_coord[0], prev_coord[1],
                coord[0], coord[1]
            )
            cumulative_distance += distance
            
            self.pole_counter += 1
            pole = NewPole(
                id=f"NEW_POLE_{self.pole_counter}",
                coord=coord,
                sequence=i + 1,
                distance_from_consumer=cumulative_distance,
                is_junction=is_junction
            )
            new_poles.append(pole)
            
            prev_coord = coord
        
        result.new_poles = new_poles
        result.total_wire_length = total_length
        result.turn_count = turn_count
        result.message = f"{len(new_poles)}개 신설 전주 배치 완료 (굴절 {turn_count}회)"
        
        logger.info(f"전주 배치: {result.message}")
        
        return result
    
    def _calculate_pole_count(self, total_distance: float) -> int:
        """
        PRD 4.1 공식에 따른 신설 전주 개수 산출
        
        공식: N = 1 + ceil((D - d₁) / d₂)
        - d₁ = 30m (첫 구간, FIRST_POLE_MAX_DISTANCE)
        - d₂ = 40m (표준 경간, POLE_INTERVAL)
        
        예시 (120m):
        1. D - d₁ = 120 - 30 = 90m
        2. (D - d₁) / d₂ = 90 / 40 = 2.25
        3. ceil(2.25) = 3
        4. N = 1 + 3 = 4본
        
        Args:
            total_distance: 총 경로 거리 (m)
        
        Returns:
            신설 전주 개수
        """
        # 첫 구간(30m) 이내면 전주 1개
        if total_distance <= self.first_pole_max_distance:
            return 1
        
        # 잔여 거리 계산
        remaining = total_distance - self.first_pole_max_distance
        
        # 추가 전주 개수 (올림)
        additional = math.ceil(remaining / self.pole_interval)
        
        return 1 + additional
    
    def _calculate_pole_positions(
        self,
        path_coords: List[Tuple[float, float]],
        total_length: float
    ) -> List[float]:
        """
        신설 전주 배치 위치 계산
        
        배치 규칙:
        1. 첫 전주: 수용가 위치(0m)에 필수 배치
        2. 이후 전주: 40m 간격으로 배치 (전주 간 거리 40m 초과 불가)
        3. 기설전주 근처(15m 이내)에는 신설 전주 배치 안함
        4. 마지막 구간(마지막 신설전주 ~ 기설전주)도 40m 이내가 되도록,
           필요 시 유효 구간 끝(기설전주 15m 전)에 전주 1개 추가
        
        Args:
            path_coords: 경로 좌표
            total_length: 총 경로 길이 (m)
        
        Returns:
            배치 위치(거리) 리스트
        """
        positions = []
        
        # 경로 길이가 너무 짧으면 (기설전주가 15m 이내) 수용가 위치에만 배치
        if total_length <= self.MIN_DISTANCE_TO_EXISTING_POLE:
            # 기설전주가 매우 가까우면 수용가 위치에 전주 1개만
            positions.append(0)
            return positions
        
        # 1. 수용가 위치(0m)에 첫 전주 필수 배치
        positions.append(0)
        
        # 2. 기설전주까지의 유효 거리 (기설전주 15m 전까지만 배치)
        effective_length = total_length - self.MIN_DISTANCE_TO_EXISTING_POLE
        
        # 유효 거리가 전주 간격보다 짧으면 더 이상 배치 안함
        if effective_length <= self.pole_interval:
            return positions
        
        # 3. 40m 간격으로 전주 배치 (전주 간 거리는 40m 초과 불가)
        current_pos = self.pole_interval
        while current_pos <= effective_length:
            positions.append(current_pos)
            current_pos += self.pole_interval
        
        # 4. 마지막 구간(마지막 전주 ~ 기설전주)도 40m 이내여야 함
        #    초과 시 유효 구간 끝(기설전주 15m 전)에 전주 1개 추가
        if positions and (total_length - positions[-1]) > self.pole_interval:
            # 기설전주 15m 이내는 배치 금지이므로, 유효 끝점에 배치
            if effective_length > positions[-1]:
                positions.append(effective_length)
        
        return positions
    
    def _find_junctions(
        self,
        path_coords: List[Tuple[float, float]],
        angle_threshold: float = 150.0
    ) -> List[Tuple[float, bool]]:
        """
        분기점 (꺾이는 지점) 찾기
        
        Args:
            path_coords: 경로 좌표
            angle_threshold: 분기점 판정 각도 임계값 (도)
        
        Returns:
            (거리, True) 튜플 리스트
        """
        junctions = []
        
        if len(path_coords) < 3:
            return junctions
        
        path_line = LineString(path_coords)
        cumulative_distance = 0.0
        
        for i in range(1, len(path_coords) - 1):
            p1 = path_coords[i - 1]
            p2 = path_coords[i]
            p3 = path_coords[i + 1]
            
            # 이전 세그먼트 거리 누적
            cumulative_distance += calculate_distance(
                p1[0], p1[1], p2[0], p2[1]
            )
            
            # 각도 계산
            angle = calculate_angle(p1, p2, p3)
            
            # 각도가 임계값 미만이면 분기점
            if angle < angle_threshold:
                junctions.append((cumulative_distance, True))
                logger.debug(f"분기점 발견: 위치 {cumulative_distance:.1f}m, 각도 {angle:.1f}°")
        
        return junctions
    
    def _merge_positions(
        self,
        regular_positions: List[float],
        junction_positions: List[Tuple[float, bool]],
        merge_threshold: float = 10.0
    ) -> List[Tuple[float, bool]]:
        """
        일반 배치 위치와 분기점 위치 병합
        
        Args:
            regular_positions: 일반 배치 위치
            junction_positions: 분기점 위치
            merge_threshold: 병합 임계 거리 (m)
        
        Returns:
            병합된 (위치, 분기점여부) 리스트
        """
        # 모든 위치를 리스트로 변환
        all_positions = [(pos, False) for pos in regular_positions]
        all_positions.extend(junction_positions)
        
        # 위치 순 정렬
        all_positions.sort(key=lambda x: x[0])
        
        # 가까운 위치 병합
        merged = []
        
        for pos, is_junction in all_positions:
            if not merged:
                merged.append((pos, is_junction))
                continue
            
            last_pos, last_is_junction = merged[-1]
            
            # 이전 위치와 가까우면 병합
            if abs(pos - last_pos) < merge_threshold:
                # 분기점 우선
                if is_junction and not last_is_junction:
                    merged[-1] = (pos, True)
            else:
                merged.append((pos, is_junction))
        
        return merged
    
    def allocate_batch(
        self,
        path_results: List[PathResult]
    ) -> List[AllocationResult]:
        """
        여러 경로에 대해 일괄 배치
        
        Args:
            path_results: 경로 결과 리스트
        
        Returns:
            배치 결과 리스트
        """
        results = []
        
        for path_result in path_results:
            result = self.allocate(path_result)
            results.append(result)
        
        return results
