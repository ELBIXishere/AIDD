"""
ELBIX AIDD 좌표 변환 유틸리티
- EPSG:3857 (Web Mercator) ↔ EPSG:32652 (UTM Zone 52N) 변환
- BBox 계산
"""

from pyproj import Transformer, CRS
from typing import Tuple, List
import math

from app.config import settings


class CoordinateTransformer:
    """좌표 변환 클래스"""
    
    def __init__(self):
        # 변환기 캐시 (성능 최적화)
        self._transformers = {}
    
    def _get_transformer(self, from_crs: str, to_crs: str) -> Transformer:
        """변환기 인스턴스 가져오기 (캐싱)"""
        key = f"{from_crs}_{to_crs}"
        if key not in self._transformers:
            self._transformers[key] = Transformer.from_crs(
                from_crs, to_crs, always_xy=True
            )
        return self._transformers[key]
    
    def transform_point(
        self,
        x: float,
        y: float,
        from_crs: str,
        to_crs: str
    ) -> Tuple[float, float]:
        """
        단일 좌표 변환
        
        Args:
            x: X 좌표
            y: Y 좌표
            from_crs: 원본 좌표계 (예: "EPSG:3857")
            to_crs: 대상 좌표계 (예: "EPSG:32652")
        
        Returns:
            변환된 (x, y) 튜플
        """
        transformer = self._get_transformer(from_crs, to_crs)
        return transformer.transform(x, y)
    
    def transform_points(
        self,
        coords: List[Tuple[float, float]],
        from_crs: str,
        to_crs: str
    ) -> List[Tuple[float, float]]:
        """
        여러 좌표 일괄 변환
        
        Args:
            coords: 좌표 리스트 [(x1, y1), (x2, y2), ...]
            from_crs: 원본 좌표계
            to_crs: 대상 좌표계
        
        Returns:
            변환된 좌표 리스트
        """
        transformer = self._get_transformer(from_crs, to_crs)
        return [transformer.transform(x, y) for x, y in coords]
    
    def input_to_process(self, x: float, y: float) -> Tuple[float, float]:
        """
        입력 좌표계(EPSG:3857) → 처리 좌표계(EPSG:32652)
        """
        return self.transform_point(
            x, y,
            settings.INPUT_CRS,
            settings.PROCESS_CRS
        )
    
    def process_to_input(self, x: float, y: float) -> Tuple[float, float]:
        """
        처리 좌표계(EPSG:32652) → 입력 좌표계(EPSG:3857)
        """
        return self.transform_point(
            x, y,
            settings.PROCESS_CRS,
            settings.INPUT_CRS
        )
    
    def input_to_wgs84(self, x: float, y: float) -> Tuple[float, float]:
        """
        입력 좌표계(EPSG:3857) → WGS84(EPSG:4326)
        """
        return self.transform_point(
            x, y,
            settings.INPUT_CRS,
            settings.WGS84_CRS
        )
    
    def wgs84_to_input(self, lon: float, lat: float) -> Tuple[float, float]:
        """
        WGS84(EPSG:4326) → 입력 좌표계(EPSG:3857)
        """
        return self.transform_point(
            lon, lat,
            settings.WGS84_CRS,
            settings.INPUT_CRS
        )


def calculate_bbox(
    center_x: float,
    center_y: float,
    size: float = None
) -> Tuple[float, float, float, float]:
    """
    중심 좌표를 기준으로 BBox 계산
    
    Args:
        center_x: 중심 X 좌표
        center_y: 중심 Y 좌표
        size: BBox 한 변의 길이 (미터, 기본값: settings.BBOX_SIZE)
    
    Returns:
        (min_x, min_y, max_x, max_y) 튜플
    """
    if size is None:
        size = settings.BBOX_SIZE
    
    half_size = size / 2
    
    return (
        center_x - half_size,  # min_x
        center_y - half_size,  # min_y
        center_x + half_size,  # max_x
        center_y + half_size   # max_y
    )


def calculate_distance(
    x1: float,
    y1: float,
    x2: float,
    y2: float
) -> float:
    """
    두 점 사이의 유클리드 거리 계산 (미터)
    
    Args:
        x1, y1: 첫 번째 점
        x2, y2: 두 번째 점
    
    Returns:
        거리 (미터)
    """
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def calculate_line_length(coords: List[Tuple[float, float]]) -> float:
    """
    선(LineString)의 총 길이 계산
    
    Args:
        coords: 좌표 리스트 [(x1, y1), (x2, y2), ...]
    
    Returns:
        총 길이 (미터)
    """
    if len(coords) < 2:
        return 0.0
    
    total = 0.0
    for i in range(len(coords) - 1):
        total += calculate_distance(
            coords[i][0], coords[i][1],
            coords[i + 1][0], coords[i + 1][1]
        )
    return total


# 전역 좌표 변환기 인스턴스
coord_transformer = CoordinateTransformer()
