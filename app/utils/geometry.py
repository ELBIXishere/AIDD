"""
ELBIX AIDD 기하학 연산 유틸리티
- Shapely를 활용한 공간 연산
"""

from shapely.geometry import Point, LineString, Polygon, MultiLineString
from shapely.ops import nearest_points, split, linemerge
from shapely import wkt
from typing import Tuple, List, Optional, Union
import math


def point_to_line_distance(
    point: Tuple[float, float],
    line_coords: List[Tuple[float, float]]
) -> float:
    """
    점에서 선까지의 최단 거리
    
    Args:
        point: 점 좌표 (x, y)
        line_coords: 선 좌표 리스트 [(x1, y1), (x2, y2), ...]
    
    Returns:
        최단 거리 (미터)
    """
    pt = Point(point)
    line = LineString(line_coords)
    return pt.distance(line)


def nearest_point_on_line(
    point: Tuple[float, float],
    line_coords: List[Tuple[float, float]]
) -> Tuple[float, float]:
    """
    선 위의 점에서 가장 가까운 점 찾기
    
    Args:
        point: 점 좌표 (x, y)
        line_coords: 선 좌표 리스트
    
    Returns:
        선 위의 가장 가까운 점 (x, y)
    """
    pt = Point(point)
    line = LineString(line_coords)
    nearest = nearest_points(pt, line)[1]
    return (nearest.x, nearest.y)


def point_in_polygon(
    point: Tuple[float, float],
    polygon_coords: List[Tuple[float, float]]
) -> bool:
    """
    점이 폴리곤 내부에 있는지 확인
    
    Args:
        point: 점 좌표 (x, y)
        polygon_coords: 폴리곤 좌표 리스트
    
    Returns:
        내부에 있으면 True
    """
    pt = Point(point)
    poly = Polygon(polygon_coords)
    return poly.contains(pt)


def line_intersects_polygon(
    line_coords: List[Tuple[float, float]],
    polygon_coords: List[Tuple[float, float]]
) -> bool:
    """
    선이 폴리곤과 교차하는지 확인
    
    Args:
        line_coords: 선 좌표 리스트
        polygon_coords: 폴리곤 좌표 리스트
    
    Returns:
        교차하면 True
    """
    line = LineString(line_coords)
    poly = Polygon(polygon_coords)
    return line.intersects(poly)


def lines_intersect(
    line1_coords: List[Tuple[float, float]],
    line2_coords: List[Tuple[float, float]]
) -> bool:
    """
    두 선이 교차하는지 확인
    
    Args:
        line1_coords: 첫 번째 선 좌표
        line2_coords: 두 번째 선 좌표
    
    Returns:
        교차하면 True
    """
    line1 = LineString(line1_coords)
    line2 = LineString(line2_coords)
    return line1.intersects(line2) and not line1.touches(line2)


def get_line_intersection_point(
    line1_coords: List[Tuple[float, float]],
    line2_coords: List[Tuple[float, float]]
) -> Optional[Tuple[float, float]]:
    """
    두 선의 교차점 반환
    
    Args:
        line1_coords: 첫 번째 선 좌표
        line2_coords: 두 번째 선 좌표
    
    Returns:
        교차점 (x, y) 또는 None
    """
    line1 = LineString(line1_coords)
    line2 = LineString(line2_coords)
    intersection = line1.intersection(line2)
    
    if intersection.is_empty:
        return None
    elif intersection.geom_type == 'Point':
        return (intersection.x, intersection.y)
    else:
        # MultiPoint 등의 경우 첫 번째 점 반환
        return (intersection.coords[0][0], intersection.coords[0][1])


def buffer_point(
    point: Tuple[float, float],
    radius: float
) -> List[Tuple[float, float]]:
    """
    점을 중심으로 원형 버퍼 생성
    
    Args:
        point: 중심점 (x, y)
        radius: 반경 (미터)
    
    Returns:
        버퍼 폴리곤 좌표
    """
    pt = Point(point)
    buffer = pt.buffer(radius)
    return list(buffer.exterior.coords)


def simplify_line(
    line_coords: List[Tuple[float, float]],
    tolerance: float = 1.0
) -> List[Tuple[float, float]]:
    """
    선 단순화 (Douglas-Peucker 알고리즘)
    
    Args:
        line_coords: 선 좌표 리스트
        tolerance: 허용 오차 (미터)
    
    Returns:
        단순화된 선 좌표
    """
    line = LineString(line_coords)
    simplified = line.simplify(tolerance, preserve_topology=True)
    return list(simplified.coords)


def interpolate_points_on_line(
    line_coords: List[Tuple[float, float]],
    interval: float
) -> List[Tuple[float, float]]:
    """
    선 위에 일정 간격으로 점 배치
    
    Args:
        line_coords: 선 좌표 리스트
        interval: 간격 (미터)
    
    Returns:
        배치된 점 좌표 리스트
    """
    line = LineString(line_coords)
    length = line.length
    
    if length == 0:
        return []
    
    points = []
    distance = 0.0
    
    while distance <= length:
        point = line.interpolate(distance)
        points.append((point.x, point.y))
        distance += interval
    
    return points


def merge_lines(
    lines: List[List[Tuple[float, float]]]
) -> List[Tuple[float, float]]:
    """
    여러 선을 하나로 병합
    
    Args:
        lines: 선 좌표 리스트의 리스트
    
    Returns:
        병합된 선 좌표
    """
    if not lines:
        return []
    
    line_strings = [LineString(coords) for coords in lines]
    merged = linemerge(line_strings)
    
    if isinstance(merged, LineString):
        return list(merged.coords)
    elif isinstance(merged, MultiLineString):
        # 병합이 완전하지 않은 경우 첫 번째 선 반환
        return list(merged.geoms[0].coords)
    else:
        return []


def calculate_angle(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    p3: Tuple[float, float]
) -> float:
    """
    세 점이 이루는 각도 계산 (도)
    
    Args:
        p1, p2, p3: 세 점 (p2가 꼭짓점)
    
    Returns:
        각도 (0 ~ 180도)
    """
    v1 = (p1[0] - p2[0], p1[1] - p2[1])
    v2 = (p3[0] - p2[0], p3[1] - p2[1])
    
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    mag1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2)
    mag2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2)
    
    if mag1 == 0 or mag2 == 0:
        return 0.0
    
    cos_angle = dot / (mag1 * mag2)
    # 부동소수점 오차 보정
    cos_angle = max(-1.0, min(1.0, cos_angle))
    
    return math.degrees(math.acos(cos_angle))


def is_point_near_line(
    point: Tuple[float, float],
    line_coords: List[Tuple[float, float]],
    threshold: float
) -> bool:
    """
    점이 선에서 특정 거리 이내에 있는지 확인
    
    Args:
        point: 점 좌표
        line_coords: 선 좌표
        threshold: 임계 거리 (미터)
    
    Returns:
        거리 이내면 True
    """
    return point_to_line_distance(point, line_coords) <= threshold


def create_line_from_points(
    start: Tuple[float, float],
    end: Tuple[float, float]
) -> List[Tuple[float, float]]:
    """
    두 점을 연결하는 선 생성
    
    Args:
        start: 시작점
        end: 끝점
    
    Returns:
        선 좌표 리스트
    """
    return [start, end]
