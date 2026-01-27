"""
ELBIX AIDD 전선 교차 검증 모듈
- FR-05: 신설 경로는 기존 고압/저압 전선과 교차할 수 없음
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from shapely.geometry import LineString, Point
import logging

from app.core.preprocessor import Line, ProcessedData

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """검증 결과"""
    is_valid: bool                       # 유효 여부 (교차 없음)
    crossing_lines: List[str] = None     # 교차하는 전선 ID 목록
    crossing_points: List[Tuple[float, float]] = None  # 교차 지점 좌표
    message: str = ""
    
    def __post_init__(self):
        if self.crossing_lines is None:
            self.crossing_lines = []
        if self.crossing_points is None:
            self.crossing_points = []


class LineValidator:
    """
    전선 교차 검증기
    
    FR-05: 신설 경로는 기존 고압/저압 전선과 교차할 수 없음
    """
    
    def __init__(self, processed_data: ProcessedData):
        """
        Args:
            processed_data: 전처리된 데이터 (기존 전선 정보 포함)
        """
        self.existing_lines = processed_data.lines
        
        # Shapely LineString 객체로 변환 (성능 최적화)
        self.line_geometries: List[Tuple[str, LineString, str]] = []
        for line in self.existing_lines:
            if line.geometry and len(line.coords) >= 2:
                self.line_geometries.append((
                    line.id,
                    line.geometry,
                    line.line_type or "unknown"
                ))
        
        logger.info(f"전선 교차 검증기 초기화: 기존 전선 {len(self.line_geometries)}개")
    
    def validate_path(
        self,
        path_coords: List[Tuple[float, float]]
    ) -> ValidationResult:
        """
        경로가 기존 전선과 교차하는지 검증
        
        Args:
            path_coords: 신설 경로 좌표 리스트
        
        Returns:
            검증 결과
        """
        if len(path_coords) < 2:
            return ValidationResult(
                is_valid=True,
                message="경로가 너무 짧아 검증 불필요"
            )
        
        # 신설 경로를 LineString으로 변환
        new_path = LineString(path_coords)
        
        crossing_lines = []
        crossing_points = []
        
        for line_id, line_geom, line_type in self.line_geometries:
            # 교차 여부 확인
            if new_path.intersects(line_geom):
                # 단순 접촉(touches)은 허용, 실제 교차(crosses)만 체크
                if new_path.crosses(line_geom) or (
                    new_path.intersects(line_geom) and not new_path.touches(line_geom)
                ):
                    # 교차 지점 계산
                    intersection = new_path.intersection(line_geom)
                    
                    # 교차점이 경로의 시작/끝점인 경우는 허용 (연결점)
                    if self._is_endpoint_intersection(intersection, path_coords):
                        continue
                    
                    crossing_lines.append(f"{line_id}({line_type})")
                    
                    # 교차 지점 좌표 추출
                    if intersection.geom_type == 'Point':
                        crossing_points.append((intersection.x, intersection.y))
                    elif intersection.geom_type == 'MultiPoint':
                        for pt in intersection.geoms:
                            crossing_points.append((pt.x, pt.y))
        
        is_valid = len(crossing_lines) == 0
        
        if is_valid:
            message = "전선 교차 없음 - 경로 유효"
        else:
            message = f"전선 교차 발생: {', '.join(crossing_lines)}"
            logger.warning(message)
        
        return ValidationResult(
            is_valid=is_valid,
            crossing_lines=crossing_lines,
            crossing_points=crossing_points,
            message=message
        )
    
    def _is_endpoint_intersection(
        self,
        intersection,
        path_coords: List[Tuple[float, float]],
        tolerance: float = 1.0
    ) -> bool:
        """
        교차점이 경로의 시작/끝점인지 확인
        
        전주와의 연결점에서의 교차는 허용
        
        Args:
            intersection: Shapely 교차 객체
            path_coords: 경로 좌표
            tolerance: 허용 오차 (m)
        
        Returns:
            시작/끝점 교차이면 True
        """
        if not path_coords:
            return False
        
        start = path_coords[0]
        end = path_coords[-1]
        
        def is_near(pt, ref, tol):
            return abs(pt[0] - ref[0]) < tol and abs(pt[1] - ref[1]) < tol
        
        if intersection.geom_type == 'Point':
            pt = (intersection.x, intersection.y)
            return is_near(pt, start, tolerance) or is_near(pt, end, tolerance)
        elif intersection.geom_type == 'MultiPoint':
            for geom in intersection.geoms:
                pt = (geom.x, geom.y)
                if not (is_near(pt, start, tolerance) or is_near(pt, end, tolerance)):
                    return False
            return True
        
        return False
    
    def validate_batch(
        self,
        paths: List[List[Tuple[float, float]]]
    ) -> List[ValidationResult]:
        """
        여러 경로 일괄 검증
        
        Args:
            paths: 경로 좌표 리스트의 리스트
        
        Returns:
            검증 결과 리스트
        """
        results = []
        for path_coords in paths:
            result = self.validate_path(path_coords)
            results.append(result)
        return results
    
    def filter_valid_paths(
        self,
        paths: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        유효한 경로만 필터링
        
        Args:
            paths: 경로 정보 딕셔너리 리스트 (path_coords 키 포함)
        
        Returns:
            교차 없는 유효 경로만 필터링
        """
        valid_paths = []
        
        for path in paths:
            coords = path.get('path_coords', [])
            result = self.validate_path(coords)
            
            if result.is_valid:
                valid_paths.append(path)
            else:
                logger.info(
                    f"경로 제외 (전선 교차): {result.message}"
                )
        
        logger.info(f"전선 교차 필터링: {len(paths)}개 → {len(valid_paths)}개")
        return valid_paths
    
    def get_crossing_info(
        self,
        path_coords: List[Tuple[float, float]]
    ) -> Dict[str, Any]:
        """
        경로의 전선 교차 상세 정보 반환
        
        Args:
            path_coords: 경로 좌표
        
        Returns:
            교차 정보 딕셔너리
        """
        result = self.validate_path(path_coords)
        
        return {
            "is_valid": result.is_valid,
            "crossing_count": len(result.crossing_lines),
            "crossing_lines": result.crossing_lines,
            "crossing_points": result.crossing_points,
            "message": result.message
        }
