"""
ELBIX AIDD 도로 네트워크 그래프 빌더
- NetworkX를 활용한 그래프 구축
- 끊긴 도로 보정 (Snapping)
- 수용가/전주 연결점 추가
"""

import networkx as nx
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import nearest_points, unary_union
import math
import logging

from app.config import settings
from app.core.preprocessor import Road, Pole, Building, ProcessedData
from app.core.target_selector import TargetPole
from app.utils.coordinate import calculate_distance
from app.utils.profiler import profile, profile_block

# R-tree 공간 인덱스 (선택적)
try:
    from rtree import index as rtree_index
    RTREE_AVAILABLE = True
except ImportError:
    RTREE_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("rtree 패키지 없음 - 해시맵 기반 인덱싱 사용")

logger = logging.getLogger(__name__)


@dataclass
class GraphNode:
    """그래프 노드"""
    id: str
    coord: Tuple[float, float]
    node_type: str = "road"  # road, consumer, pole, junction
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, GraphNode):
            return self.id == other.id
        return False


@dataclass
class GraphEdge:
    """그래프 엣지"""
    from_node: str
    to_node: str
    distance: float           # 거리 (m)
    weight: float            # 가중치 (비용 반영)
    geometry: Optional[LineString] = None
    edge_type: str = "road"  # road, connection


@dataclass
class RoadGraph:
    """도로 네트워크 그래프"""
    graph: nx.Graph
    nodes: Dict[str, GraphNode] = field(default_factory=dict)
    consumer_node_id: Optional[str] = None
    pole_node_ids: List[str] = field(default_factory=list)


class SpatialIndex:
    """
    공간 인덱스 (R-tree 또는 해시맵)
    
    - R-tree 가용 시: O(log n) 최근접 탐색
    - R-tree 불가 시: 해시맵 기반 O(1) 조회 + 선형 탐색 폴백
    """
    
    def __init__(self, precision: float = 1.0):
        """
        Args:
            precision: 좌표 해시 정밀도 (미터, 기본 1m)
        """
        self.precision = precision
        self.nodes: Dict[str, Tuple[float, float]] = {}  # node_id → coord
        
        # 해시맵: 격자 기반 공간 인덱스
        self.grid: Dict[Tuple[int, int], List[str]] = {}
        
        # R-tree 인덱스 (가용 시)
        self.rtree = None
        self.rtree_id_map: Dict[int, str] = {}  # rtree_id → node_id
        self.next_rtree_id = 0
        
        if RTREE_AVAILABLE:
            self.rtree = rtree_index.Index()
    
    def _grid_key(self, coord: Tuple[float, float]) -> Tuple[int, int]:
        """좌표를 격자 키로 변환"""
        return (
            int(coord[0] / self.precision),
            int(coord[1] / self.precision)
        )
    
    def insert(self, node_id: str, coord: Tuple[float, float]):
        """노드 추가"""
        self.nodes[node_id] = coord
        
        # 해시맵에 추가
        grid_key = self._grid_key(coord)
        if grid_key not in self.grid:
            self.grid[grid_key] = []
        self.grid[grid_key].append(node_id)
        
        # R-tree에 추가
        if self.rtree:
            rtree_id = self.next_rtree_id
            self.rtree_id_map[rtree_id] = node_id
            self.rtree.insert(rtree_id, (coord[0], coord[1], coord[0], coord[1]))
            self.next_rtree_id += 1
    
    def find_nearest(
        self,
        coord: Tuple[float, float],
        tolerance: float = 1.0
    ) -> Optional[str]:
        """
        가장 가까운 노드 찾기
        
        Args:
            coord: 검색 좌표
            tolerance: 허용 거리 (미터)
        
        Returns:
            노드 ID 또는 None
        """
        # R-tree 사용 가능 시: O(log n)
        if self.rtree:
            nearby = list(self.rtree.nearest(
                (coord[0], coord[1], coord[0], coord[1]), 1
            ))
            if nearby:
                node_id = self.rtree_id_map.get(nearby[0])
                if node_id and node_id in self.nodes:
                    node_coord = self.nodes[node_id]
                    if calculate_distance(coord[0], coord[1], node_coord[0], node_coord[1]) < tolerance:
                        return node_id
            return None
        
        # 해시맵 기반: 주변 격자 탐색
        grid_key = self._grid_key(coord)
        search_range = int(tolerance / self.precision) + 1
        
        min_dist = float('inf')
        nearest_node = None
        
        for dx in range(-search_range, search_range + 1):
            for dy in range(-search_range, search_range + 1):
                check_key = (grid_key[0] + dx, grid_key[1] + dy)
                if check_key in self.grid:
                    for node_id in self.grid[check_key]:
                        node_coord = self.nodes[node_id]
                        dist = calculate_distance(
                            coord[0], coord[1],
                            node_coord[0], node_coord[1]
                        )
                        if dist < tolerance and dist < min_dist:
                            min_dist = dist
                            nearest_node = node_id
        
        return nearest_node
    
    def find_in_radius(
        self,
        coord: Tuple[float, float],
        radius: float
    ) -> List[str]:
        """
        반경 내 모든 노드 찾기
        
        Args:
            coord: 중심 좌표
            radius: 검색 반경 (미터)
        
        Returns:
            노드 ID 리스트
        """
        result = []
        
        # R-tree 사용 가능 시
        if self.rtree:
            bbox = (
                coord[0] - radius, coord[1] - radius,
                coord[0] + radius, coord[1] + radius
            )
            nearby_ids = list(self.rtree.intersection(bbox))
            for rtree_id in nearby_ids:
                node_id = self.rtree_id_map.get(rtree_id)
                if node_id and node_id in self.nodes:
                    node_coord = self.nodes[node_id]
                    if calculate_distance(coord[0], coord[1], node_coord[0], node_coord[1]) <= radius:
                        result.append(node_id)
            return result
        
        # 해시맵 기반
        grid_key = self._grid_key(coord)
        search_range = int(radius / self.precision) + 1
        
        for dx in range(-search_range, search_range + 1):
            for dy in range(-search_range, search_range + 1):
                check_key = (grid_key[0] + dx, grid_key[1] + dy)
                if check_key in self.grid:
                    for node_id in self.grid[check_key]:
                        node_coord = self.nodes[node_id]
                        if calculate_distance(coord[0], coord[1], node_coord[0], node_coord[1]) <= radius:
                            result.append(node_id)
        
        return result


class RoadGraphBuilder:
    """도로 네트워크 그래프 빌더 (공간 인덱싱 적용)"""
    
    def __init__(self, processed_data: ProcessedData):
        """
        Args:
            processed_data: 전처리된 데이터
        """
        self.data = processed_data
        self.roads = processed_data.roads
        self.buildings = processed_data.buildings
        
        # 건물 폴리곤 병합 (성능 최적화)
        if self.buildings:
            self.building_union = unary_union([b.geometry for b in self.buildings])
        else:
            self.building_union = None
        
        # 그래프 초기화
        self.graph = nx.Graph()
        self.nodes: Dict[str, GraphNode] = {}
        self.node_counter = 0
        
        # 공간 인덱스 초기화
        self.spatial_index = SpatialIndex(precision=1.0)
    
    @profile
    def build(
        self,
        consumer_coord: Tuple[float, float],
        target_poles: List[TargetPole]
    ) -> RoadGraph:
        """
        도로 네트워크 그래프 구축 (공간 인덱싱 적용)
        
        Args:
            consumer_coord: 수용가 좌표
            target_poles: 후보 전주 목록
        
        Returns:
            구축된 그래프
        """
        logger.info(f"그래프 구축 시작: 도로 {len(self.roads)}개, 후보 전주 {len(target_poles)}개")
        
        # Step 1: 도로 중심선을 그래프로 변환
        with profile_block("도로 그래프 변환"):
            self._build_road_graph()
        
        logger.info(f"도로 그래프: 노드 {self.graph.number_of_nodes()}개, 엣지 {self.graph.number_of_edges()}개")
        
        # Step 2: 끊긴 도로 보정 (Snapping)
        with profile_block("도로 스냅핑"):
            self._snap_disconnected_roads()
        
        logger.info(f"스냅핑 후: 노드 {self.graph.number_of_nodes()}개, 엣지 {self.graph.number_of_edges()}개")
        
        # Step 3: 수용가 연결점 추가
        with profile_block("수용가 연결"):
            consumer_node_id = self._add_consumer_node(consumer_coord)
        
        # Step 4: 전주 연결점 추가
        with profile_block("전주 연결"):
            pole_node_ids = self._add_pole_nodes(target_poles)
        
        logger.info(f"최종 그래프: 노드 {self.graph.number_of_nodes()}개, 엣지 {self.graph.number_of_edges()}개")
        
        return RoadGraph(
            graph=self.graph,
            nodes=self.nodes,
            consumer_node_id=consumer_node_id,
            pole_node_ids=pole_node_ids
        )
    
    def _build_road_graph(self):
        """도로 중심선을 그래프의 Node/Edge로 변환"""
        for road in self.roads:
            coords = road.coords
            
            if len(coords) < 2:
                continue
            
            # 도로의 각 세그먼트를 엣지로 추가
            for i in range(len(coords) - 1):
                start_coord = coords[i]
                end_coord = coords[i + 1]
                
                # 노드 생성/조회
                start_node = self._get_or_create_node(start_coord, "road")
                end_node = self._get_or_create_node(end_coord, "road")
                
                # 거리 계산
                distance = calculate_distance(
                    start_coord[0], start_coord[1],
                    end_coord[0], end_coord[1]
                )
                
                # 가중치 계산 (거리 + 전주 비용 반영)
                weight = self._calculate_weight(distance)
                
                # 엣지 추가
                self.graph.add_edge(
                    start_node.id,
                    end_node.id,
                    distance=distance,
                    weight=weight,
                    edge_type="road",
                    geometry=LineString([start_coord, end_coord])
                )
    
    def _get_or_create_node(
        self,
        coord: Tuple[float, float],
        node_type: str,
        tolerance: float = 1.0
    ) -> GraphNode:
        """
        좌표에 해당하는 노드 조회 또는 생성 (공간 인덱스 활용)
        
        Args:
            coord: 좌표
            node_type: 노드 타입
            tolerance: 동일 노드 판정 허용 오차 (m)
        
        Returns:
            GraphNode
        """
        # 공간 인덱스로 가까운 노드 찾기 (O(log n) 또는 O(1))
        existing_node_id = self.spatial_index.find_nearest(coord, tolerance)
        if existing_node_id and existing_node_id in self.nodes:
            return self.nodes[existing_node_id]
        
        # 새 노드 생성
        self.node_counter += 1
        node_id = f"N{self.node_counter}"
        
        node = GraphNode(
            id=node_id,
            coord=coord,
            node_type=node_type
        )
        
        self.nodes[node_id] = node
        self.graph.add_node(node_id, coord=coord, node_type=node_type)
        
        # 공간 인덱스에 추가
        self.spatial_index.insert(node_id, coord)
        
        return node
    
    def _snap_disconnected_roads(self):
        """
        끊긴 도로 연결 (Snapping)
        - 10m 이내의 끊긴 노드를 연결
        """
        snap_distance = settings.ROAD_SNAP_DISTANCE
        
        # Degree가 1인 노드 (끝점) 찾기
        end_nodes = [
            node_id for node_id in self.graph.nodes()
            if self.graph.degree(node_id) == 1
        ]
        
        # 끝점들 간의 거리 체크 및 연결
        connected_pairs: Set[Tuple[str, str]] = set()
        
        for i, node1_id in enumerate(end_nodes):
            for node2_id in end_nodes[i + 1:]:
                if node1_id == node2_id:
                    continue
                
                # 이미 연결된 쌍 스킵
                pair = tuple(sorted([node1_id, node2_id]))
                if pair in connected_pairs:
                    continue
                
                # 거리 계산
                coord1 = self.nodes[node1_id].coord
                coord2 = self.nodes[node2_id].coord
                distance = calculate_distance(
                    coord1[0], coord1[1],
                    coord2[0], coord2[1]
                )
                
                # 스냅 거리 이내면 연결
                if distance <= snap_distance:
                    weight = self._calculate_weight(distance)
                    self.graph.add_edge(
                        node1_id,
                        node2_id,
                        distance=distance,
                        weight=weight,
                        edge_type="snap",
                        geometry=LineString([coord1, coord2])
                    )
                    connected_pairs.add(pair)
                    logger.debug(f"스냅 연결: {node1_id} - {node2_id} ({distance:.1f}m)")
    
    def _add_consumer_node(self, consumer_coord: Tuple[float, float]) -> str:
        """
        수용가 노드를 그래프에 추가하고 도로와 연결
        
        Args:
            consumer_coord: 수용가 좌표
        
        Returns:
            수용가 노드 ID
        """
        # 수용가 노드 생성
        consumer_node = GraphNode(
            id="CONSUMER",
            coord=consumer_coord,
            node_type="consumer"
        )
        self.nodes[consumer_node.id] = consumer_node
        self.graph.add_node(
            consumer_node.id,
            coord=consumer_coord,
            node_type="consumer"
        )
        
        # 가장 가까운 도로 찾기 및 연결
        self._connect_point_to_road(consumer_coord, consumer_node.id)
        
        return consumer_node.id
    
    def _add_pole_nodes(self, target_poles: List[TargetPole]) -> List[str]:
        """
        전주 노드들을 그래프에 추가하고 도로와 연결
        
        Args:
            target_poles: 후보 전주 목록
        
        Returns:
            전주 노드 ID 목록
        """
        pole_node_ids = []
        
        for target in target_poles:
            pole_coord = target.coord
            pole_id = f"POLE_{target.id}"
            
            # 전주 노드 생성
            pole_node = GraphNode(
                id=pole_id,
                coord=pole_coord,
                node_type="pole"
            )
            self.nodes[pole_id] = pole_node
            self.graph.add_node(
                pole_id,
                coord=pole_coord,
                node_type="pole",
                target_pole=target
            )
            
            # 도로와 연결
            connected = self._connect_point_to_road(pole_coord, pole_id)
            
            if connected:
                pole_node_ids.append(pole_id)
            else:
                # 연결 실패 시 노드 제거
                self.graph.remove_node(pole_id)
                del self.nodes[pole_id]
                logger.warning(f"전주 {target.id}을 도로와 연결할 수 없습니다.")
        
        return pole_node_ids
    
    def _check_building_intersection(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float]
    ) -> bool:
        """
        두 점 사이의 직선이 건물과 교차하는지 확인
        
        Args:
            start: 시작점
            end: 끝점
        
        Returns:
            건물과 교차하면 True
        """
        if self.building_union is None:
            return False
        
        line = LineString([start, end])
        return line.intersects(self.building_union) and not line.touches(self.building_union)
    
    def _create_bypass_path(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        max_turns: int = 2
    ) -> Optional[List[Tuple[float, float]]]:
        """
        건물 회피 우회 경로 생성 (최대 2회 굴절)
        
        FR-05: 인입 구간에 건물이 있을 경우 최대 2회 굴절하여 우회 경로 생성
        
        Args:
            start: 시작점 (수용가 또는 도로 연결점)
            end: 끝점 (전주 또는 도로 연결점)
            max_turns: 최대 굴절 횟수 (기본 2회)
        
        Returns:
            우회 경로 좌표 리스트 또는 None (우회 불가)
        """
        # 건물이 없거나 직선 연결 가능하면 직접 연결
        if not self._check_building_intersection(start, end):
            return [start, end]
        
        if self.building_union is None:
            return [start, end]
        
        # 1회 굴절 시도: L자형 우회
        # 수평-수직 또는 수직-수평 경로 시도
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        
        # 시도 1: 수평 → 수직 (└ 또는 ┘ 형태)
        corner1 = (end[0], start[1])  # 먼저 X 방향 이동
        path1 = [start, corner1, end]
        if not self._check_building_intersection(start, corner1) and \
           not self._check_building_intersection(corner1, end):
            logger.debug(f"1회 굴절 우회 성공 (수평→수직): {path1}")
            return path1
        
        # 시도 2: 수직 → 수평 (┐ 또는 ┌ 형태)
        corner2 = (start[0], end[1])  # 먼저 Y 방향 이동
        path2 = [start, corner2, end]
        if not self._check_building_intersection(start, corner2) and \
           not self._check_building_intersection(corner2, end):
            logger.debug(f"1회 굴절 우회 성공 (수직→수평): {path2}")
            return path2
        
        # 2회 굴절 시도: 건물 주변을 돌아가는 경로
        if max_turns >= 2:
            # 건물의 경계 박스를 활용한 우회
            bypass_path = self._try_two_turn_bypass(start, end)
            if bypass_path:
                logger.debug(f"2회 굴절 우회 성공: {bypass_path}")
                return bypass_path
        
        # 우회 실패
        logger.warning(f"건물 회피 우회 실패: {start} → {end}")
        return None
    
    def _try_two_turn_bypass(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float]
    ) -> Optional[List[Tuple[float, float]]]:
        """
        2회 굴절 우회 경로 시도
        
        건물 경계를 따라 우회하는 경로 생성
        
        Args:
            start: 시작점
            end: 끝점
        
        Returns:
            우회 경로 또는 None
        """
        if self.building_union is None:
            return None
        
        # 직선 경로와 교차하는 건물 찾기
        direct_line = LineString([start, end])
        
        # 교차하는 건물의 경계 좌표 구하기
        try:
            intersection = direct_line.intersection(self.building_union)
            if intersection.is_empty:
                return [start, end]
            
            # 건물 경계에서 우회점 후보 생성
            # 건물의 convex hull을 사용해 단순화
            if hasattr(self.building_union, 'convex_hull'):
                hull = self.building_union.convex_hull
                if hasattr(hull, 'exterior'):
                    hull_coords = list(hull.exterior.coords)
                else:
                    return None
            else:
                return None
            
            # 시작점과 끝점에서 가장 가까운 건물 외곽 점 찾기
            start_pt = Point(start)
            end_pt = Point(end)
            
            # 버퍼 거리 (건물에서 떨어진 거리)
            buffer_dist = 5.0  # 5m
            
            # 각 외곽점을 통과하는 경로 테스트
            best_path = None
            best_length = float('inf')
            
            for i, coord in enumerate(hull_coords[:-1]):  # 마지막 점은 첫 점과 동일
                # 외곽점에서 버퍼만큼 떨어진 위치
                # 건물 중심에서 바깥쪽으로
                center_x = sum(c[0] for c in hull_coords[:-1]) / len(hull_coords[:-1])
                center_y = sum(c[1] for c in hull_coords[:-1]) / len(hull_coords[:-1])
                
                # 외곽 방향 벡터
                dx = coord[0] - center_x
                dy = coord[1] - center_y
                dist = math.sqrt(dx*dx + dy*dy)
                if dist > 0:
                    dx /= dist
                    dy /= dist
                
                waypoint = (coord[0] + dx * buffer_dist, coord[1] + dy * buffer_dist)
                
                # 시작 → 경유점 → 끝 경로 테스트
                if not self._check_building_intersection(start, waypoint) and \
                   not self._check_building_intersection(waypoint, end):
                    path_length = (
                        calculate_distance(start[0], start[1], waypoint[0], waypoint[1]) +
                        calculate_distance(waypoint[0], waypoint[1], end[0], end[1])
                    )
                    if path_length < best_length:
                        best_length = path_length
                        best_path = [start, waypoint, end]
            
            return best_path
            
        except Exception as e:
            logger.warning(f"2회 굴절 우회 계산 오류: {e}")
            return None
    
    def _connect_point_to_road(
        self,
        point_coord: Tuple[float, float],
        point_node_id: str
    ) -> bool:
        """
        점을 가장 가까운 도로에 연결
        
        Args:
            point_coord: 점 좌표
            point_node_id: 점 노드 ID
        
        Returns:
            연결 성공 여부
        """
        point = Point(point_coord)
        
        # 모든 도로에서 가장 가까운 점 찾기
        min_distance = float('inf')
        nearest_edge = None
        nearest_point_on_road = None
        
        for u, v, data in self.graph.edges(data=True):
            if data.get("edge_type") not in ["road", "snap"]:
                continue
            
            geometry = data.get("geometry")
            if not geometry:
                coord1 = self.nodes[u].coord
                coord2 = self.nodes[v].coord
                geometry = LineString([coord1, coord2])
            
            # 도로 위의 가장 가까운 점
            nearest = nearest_points(point, geometry)[1]
            distance = point.distance(nearest)
            
            if distance < min_distance:
                min_distance = distance
                nearest_edge = (u, v, data)
                nearest_point_on_road = (nearest.x, nearest.y)
        
        # 도로 접근성 거리 체크
        if min_distance > settings.ROAD_ACCESS_DISTANCE:
            logger.warning(
                f"점({point_node_id})이 도로에서 너무 멀리 있습니다: {min_distance:.1f}m"
            )
            return False
        
        if nearest_edge is None:
            return False
        
        u, v, edge_data = nearest_edge
        
        # 도로 위 연결점이 기존 노드와 가까우면 그 노드 사용
        for node_id in [u, v]:
            node_coord = self.nodes[node_id].coord
            if calculate_distance(
                nearest_point_on_road[0], nearest_point_on_road[1],
                node_coord[0], node_coord[1]
            ) < 1.0:
                # 기존 노드에 직접 연결
                weight = self._calculate_weight(min_distance)
                self.graph.add_edge(
                    point_node_id,
                    node_id,
                    distance=min_distance,
                    weight=weight,
                    edge_type="connection"
                )
                return True
        
        # 도로 위에 새 노드 생성
        road_node = self._get_or_create_node(nearest_point_on_road, "junction")
        
        # 기존 엣지 제거하고 분할
        old_distance = edge_data.get("distance", 0)
        
        # 점 → 도로 연결점
        weight1 = self._calculate_weight(min_distance)
        self.graph.add_edge(
            point_node_id,
            road_node.id,
            distance=min_distance,
            weight=weight1,
            edge_type="connection"
        )
        
        # 도로 연결점 → 기존 노드들 (엣지 분할)
        coord_u = self.nodes[u].coord
        coord_v = self.nodes[v].coord
        
        dist_to_u = calculate_distance(
            nearest_point_on_road[0], nearest_point_on_road[1],
            coord_u[0], coord_u[1]
        )
        dist_to_v = calculate_distance(
            nearest_point_on_road[0], nearest_point_on_road[1],
            coord_v[0], coord_v[1]
        )
        
        # 기존 엣지 제거
        if self.graph.has_edge(u, v):
            self.graph.remove_edge(u, v)
        
        # 새 엣지 추가
        self.graph.add_edge(
            road_node.id,
            u,
            distance=dist_to_u,
            weight=self._calculate_weight(dist_to_u),
            edge_type="road"
        )
        self.graph.add_edge(
            road_node.id,
            v,
            distance=dist_to_v,
            weight=self._calculate_weight(dist_to_v),
            edge_type="road"
        )
        
        return True
    
    def _calculate_weight(self, distance: float) -> float:
        """
        엣지 가중치 계산
        
        가중치 = 거리 × 거리가중치 + 전주비용가중치
        (40m마다 전주 1개 필요하므로 거리에 비례하여 전주 비용 반영)
        
        Args:
            distance: 거리 (m)
        
        Returns:
            가중치
        """
        # 기본 거리 가중치
        weight = distance * settings.WEIGHT_DISTANCE
        
        # 전주 비용 가중치 (40m당 전주 1개)
        # 거리에 비례하여 전주 비용 반영
        weight += (distance / settings.POLE_INTERVAL) * settings.COST_POLE / 100
        
        return weight
    
    def get_graph(self) -> nx.Graph:
        """구축된 그래프 반환"""
        return self.graph
    
    def get_node_coord(self, node_id: str) -> Optional[Tuple[float, float]]:
        """노드 좌표 반환"""
        if node_id in self.nodes:
            return self.nodes[node_id].coord
        return None
