"""
ELBIX AIDD 경로 탐색 엔진
- A* 알고리즘 (휴리스틱 기반 최적화)
- 조기 종료 (Early Termination)
- 다중 경로 탐색 및 비교
"""

import networkx as nx
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from heapq import heappush, heappop
import logging
import math

from app.config import settings
from app.core.graph_builder import RoadGraph, GraphNode
from app.core.target_selector import TargetPole
from app.utils.coordinate import calculate_distance, calculate_line_length
from app.utils.profiler import profile, profile_block

logger = logging.getLogger(__name__)


@dataclass
class PathResult:
    """경로 탐색 결과"""
    target_pole_id: str                  # 목표 전주 ID (원본)
    target_node_id: str                  # 그래프 노드 ID
    target_coord: Tuple[float, float]    # 전주 좌표
    path_nodes: List[str]                # 경로 노드 ID 리스트
    path_coords: List[Tuple[float, float]]  # 경로 좌표 리스트
    total_distance: float                # 총 거리 (m)
    total_weight: float                  # 총 가중치 (비용 기반)
    is_reachable: bool = True            # 도달 가능 여부
    is_fast_track: bool = False          # Fast Track 여부


@dataclass
class PathfindingResult:
    """전체 경로 탐색 결과"""
    consumer_coord: Tuple[float, float]
    paths: List[PathResult] = field(default_factory=list)
    fast_track_path: Optional[PathResult] = None
    message: str = ""


class Pathfinder:
    """경로 탐색 엔진 (A* 알고리즘 적용)"""
    
    def __init__(self, road_graph: RoadGraph, use_astar: bool = True):
        """
        Args:
            road_graph: 구축된 도로 네트워크 그래프
            use_astar: A* 알고리즘 사용 여부 (기본 True)
        """
        self.road_graph = road_graph
        self.graph = road_graph.graph
        self.nodes = road_graph.nodes
        self.consumer_node_id = road_graph.consumer_node_id
        self.pole_node_ids = road_graph.pole_node_ids
        self.use_astar = use_astar
        
        # 휴리스틱 캐시 (목표 노드별)
        self._heuristic_cache: Dict[Tuple[str, str], float] = {}
    
    @profile
    def find_paths(
        self,
        target_poles: List[TargetPole],
        max_paths: int = 10
    ) -> PathfindingResult:
        """
        모든 후보 전주에 대해 경로 탐색 (A* 알고리즘 적용)
        
        Args:
            target_poles: 후보 전주 목록
            max_paths: 최대 반환 경로 수
        
        Returns:
            경로 탐색 결과
        """
        consumer_coord = self.nodes[self.consumer_node_id].coord
        
        result = PathfindingResult(
            consumer_coord=consumer_coord
        )
        
        paths: List[PathResult] = []
        
        # Fast Track 경로 먼저 체크
        fast_track_targets = [t for t in target_poles if t.is_fast_track]
        if fast_track_targets:
            target = fast_track_targets[0]
            fast_track_path = PathResult(
                target_pole_id=target.id,
                target_node_id=f"POLE_{target.id}",
                target_coord=target.coord,
                path_nodes=[self.consumer_node_id, f"POLE_{target.id}"],
                path_coords=[consumer_coord, target.coord],
                total_distance=target.distance_to_consumer,
                total_weight=target.distance_to_consumer,
                is_fast_track=True
            )
            result.fast_track_path = fast_track_path
            paths.append(fast_track_path)
            logger.info(f"Fast Track 경로: {target.id} ({target.distance_to_consumer:.1f}m)")
        
        # 후보 전주를 직선 거리순으로 정렬 (조기 종료 최적화)
        sorted_targets = sorted(
            [t for t in target_poles if not t.is_fast_track],
            key=lambda t: t.distance_to_consumer
        )
        
        # 각 전주에 대해 A* 경로 탐색
        for target in sorted_targets:
            pole_node_id = f"POLE_{target.id}"
            
            if pole_node_id not in self.graph:
                continue
            
            # A* 또는 Dijkstra 선택
            if self.use_astar:
                path_result = self._astar_path(
                    self.consumer_node_id,
                    pole_node_id,
                    target,
                    max_distance=settings.MAX_DISTANCE_LIMIT
                )
            else:
                path_result = self._dijkstra_path(
                    self.consumer_node_id,
                    pole_node_id,
                    target
                )
            
            if path_result and path_result.is_reachable:
                if path_result.total_distance <= settings.MAX_DISTANCE_LIMIT:
                    paths.append(path_result)
        
        # 가중치(비용) 순으로 정렬
        paths.sort(key=lambda p: p.total_weight)
        
        # 상위 N개만 반환
        result.paths = paths[:max_paths]
        result.message = f"{len(result.paths)}개 유효 경로 탐색 완료 (A*={self.use_astar})"
        
        logger.info(result.message)
        
        return result
    
    def _euclidean_heuristic(
        self,
        node_id: str,
        target_id: str
    ) -> float:
        """
        A* 휴리스틱 함수 (유클리드 거리)
        
        Args:
            node_id: 현재 노드 ID
            target_id: 목표 노드 ID
        
        Returns:
            휴리스틱 값 (추정 거리)
        """
        cache_key = (node_id, target_id)
        if cache_key in self._heuristic_cache:
            return self._heuristic_cache[cache_key]
        
        n1 = self.nodes[node_id].coord
        n2 = self.nodes[target_id].coord
        h = math.sqrt((n2[0] - n1[0])**2 + (n2[1] - n1[1])**2)
        
        self._heuristic_cache[cache_key] = h
        return h
    
    @profile
    def _astar_path(
        self,
        source: str,
        target: str,
        target_pole: TargetPole,
        max_distance: float = None
    ) -> Optional[PathResult]:
        """
        A* 알고리즘으로 최단 가중치 경로 탐색 (휴리스틱 적용)
        
        Args:
            source: 시작 노드 ID (수용가)
            target: 목표 노드 ID (전주)
            target_pole: 목표 전주 정보
            max_distance: 최대 탐색 거리 (조기 종료)
        
        Returns:
            경로 결과 또는 None
        """
        if max_distance is None:
            max_distance = settings.MAX_DISTANCE_LIMIT
        
        try:
            # A* 휴리스틱 함수 정의
            def heuristic(n1, n2):
                return self._euclidean_heuristic(n1, n2)
            
            # NetworkX의 astar_path 사용
            path_nodes = nx.astar_path(
                self.graph,
                source,
                target,
                heuristic=heuristic,
                weight='weight'
            )
            
            # 경로 좌표 및 거리 추출
            path_coords = []
            total_distance = 0.0
            total_weight = 0.0
            
            for i, node_id in enumerate(path_nodes):
                coord = self.nodes[node_id].coord
                path_coords.append(coord)
                
                if i > 0:
                    prev_node = path_nodes[i - 1]
                    edge_data = self.graph.get_edge_data(prev_node, node_id)
                    if edge_data:
                        total_distance += edge_data.get('distance', 0)
                        total_weight += edge_data.get('weight', 0)
                    
                    # 조기 종료: 최대 거리 초과 시 중단
                    if total_distance > max_distance:
                        return PathResult(
                            target_pole_id=target_pole.id,
                            target_node_id=target,
                            target_coord=target_pole.coord,
                            path_nodes=[],
                            path_coords=[],
                            total_distance=float('inf'),
                            total_weight=float('inf'),
                            is_reachable=False
                        )
            
            return PathResult(
                target_pole_id=target_pole.id,
                target_node_id=target,
                target_coord=target_pole.coord,
                path_nodes=path_nodes,
                path_coords=path_coords,
                total_distance=total_distance,
                total_weight=total_weight,
                is_reachable=True
            )
            
        except nx.NetworkXNoPath:
            logger.debug(f"전주 {target_pole.id}까지 경로가 없습니다.")
            return PathResult(
                target_pole_id=target_pole.id,
                target_node_id=target,
                target_coord=target_pole.coord,
                path_nodes=[],
                path_coords=[],
                total_distance=float('inf'),
                total_weight=float('inf'),
                is_reachable=False
            )
        except Exception as e:
            logger.error(f"A* 경로 탐색 오류 ({target_pole.id}): {e}")
            return None
    
    def _dijkstra_path(
        self,
        source: str,
        target: str,
        target_pole: TargetPole
    ) -> Optional[PathResult]:
        """
        Dijkstra 알고리즘으로 최단 가중치 경로 탐색 (폴백용)
        
        Args:
            source: 시작 노드 ID (수용가)
            target: 목표 노드 ID (전주)
            target_pole: 목표 전주 정보
        
        Returns:
            경로 결과 또는 None
        """
        try:
            path_nodes = nx.dijkstra_path(
                self.graph,
                source,
                target,
                weight='weight'
            )
            
            path_coords = []
            total_distance = 0.0
            total_weight = 0.0
            
            for i, node_id in enumerate(path_nodes):
                coord = self.nodes[node_id].coord
                path_coords.append(coord)
                
                if i > 0:
                    prev_node = path_nodes[i - 1]
                    edge_data = self.graph.get_edge_data(prev_node, node_id)
                    if edge_data:
                        total_distance += edge_data.get('distance', 0)
                        total_weight += edge_data.get('weight', 0)
            
            return PathResult(
                target_pole_id=target_pole.id,
                target_node_id=target,
                target_coord=target_pole.coord,
                path_nodes=path_nodes,
                path_coords=path_coords,
                total_distance=total_distance,
                total_weight=total_weight,
                is_reachable=True
            )
            
        except nx.NetworkXNoPath:
            logger.debug(f"전주 {target_pole.id}까지 경로가 없습니다.")
            return PathResult(
                target_pole_id=target_pole.id,
                target_node_id=target,
                target_coord=target_pole.coord,
                path_nodes=[],
                path_coords=[],
                total_distance=float('inf'),
                total_weight=float('inf'),
                is_reachable=False
            )
        except Exception as e:
            logger.error(f"경로 탐색 오류 ({target_pole.id}): {e}")
            return None
    
    def find_k_shortest_paths(
        self,
        target_pole: TargetPole,
        k: int = 3
    ) -> List[PathResult]:
        """
        K개의 최단 경로 탐색 (Yen's Algorithm)
        
        Args:
            target_pole: 목표 전주
            k: 찾을 경로 수
        
        Returns:
            경로 결과 리스트
        """
        pole_node_id = f"POLE_{target_pole.id}"
        
        if pole_node_id not in self.graph:
            return []
        
        try:
            # NetworkX의 k_shortest_paths 사용
            paths_generator = nx.shortest_simple_paths(
                self.graph,
                self.consumer_node_id,
                pole_node_id,
                weight='weight'
            )
            
            results = []
            for i, path_nodes in enumerate(paths_generator):
                if i >= k:
                    break
                
                # 경로 좌표 및 거리 계산
                path_coords = []
                total_distance = 0.0
                total_weight = 0.0
                
                for j, node_id in enumerate(path_nodes):
                    coord = self.nodes[node_id].coord
                    path_coords.append(coord)
                    
                    if j > 0:
                        prev_node = path_nodes[j - 1]
                        edge_data = self.graph.get_edge_data(prev_node, node_id)
                        if edge_data:
                            total_distance += edge_data.get('distance', 0)
                            total_weight += edge_data.get('weight', 0)
                
                # 400m 제한 체크
                if total_distance > settings.MAX_DISTANCE_LIMIT:
                    continue
                
                results.append(PathResult(
                    target_pole_id=target_pole.id,
                    target_node_id=pole_node_id,
                    target_coord=target_pole.coord,
                    path_nodes=list(path_nodes),
                    path_coords=path_coords,
                    total_distance=total_distance,
                    total_weight=total_weight,
                    is_reachable=True
                ))
            
            return results
            
        except nx.NetworkXNoPath:
            return []
        except Exception as e:
            logger.error(f"K-최단 경로 탐색 오류: {e}")
            return []
    
    def find_all_paths_within_distance(
        self,
        target_poles: List[TargetPole],
        max_distance: float = None
    ) -> List[PathResult]:
        """
        지정 거리 이내의 모든 유효 경로 탐색
        
        Args:
            target_poles: 후보 전주 목록
            max_distance: 최대 거리 (기본: 400m)
        
        Returns:
            유효 경로 리스트
        """
        if max_distance is None:
            max_distance = settings.MAX_DISTANCE_LIMIT
        
        all_paths = []
        
        for target in target_poles:
            # 단일 최단 경로
            path = self._dijkstra_path(
                self.consumer_node_id,
                f"POLE_{target.id}",
                target
            )
            
            if path and path.is_reachable and path.total_distance <= max_distance:
                all_paths.append(path)
        
        # 가중치 순 정렬
        all_paths.sort(key=lambda p: p.total_weight)
        
        return all_paths
