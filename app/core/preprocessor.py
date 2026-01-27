"""
ELBIX AIDD 데이터 전처리기
- WFS 데이터 정제 및 Shapely 객체 변환
- 메모리 최적화 (__slots__, 지연 로딩)
"""

from typing import List, Dict, Any, Optional, Tuple, Iterator
from dataclasses import dataclass, field
from shapely.geometry import Point, LineString, Polygon, shape
from shapely.ops import unary_union
import logging

from app.config import settings
from app.utils.profiler import profile, profile_block

logger = logging.getLogger(__name__)


@dataclass
class Pole:
    """전주 데이터 클래스"""
    id: str                          # 전주 ID
    geometry: Point                  # 위치 (Shapely Point)
    coord: Tuple[float, float]       # 좌표 (x, y)
    pole_type: Optional[str] = None  # 전주 타입 (H: 고압, L: 저압, G: 지지주)
    phase_code: Optional[str] = None # 상 코드 (1: 단상, 3: 3상)
    properties: Dict[str, Any] = field(default_factory=dict)  # 기타 속성
    
    @property
    def is_high_voltage(self) -> bool:
        """고압 전주 여부"""
        return self.pole_type == "H"
    
    @property
    def is_three_phase(self) -> bool:
        """3상 전주 여부"""
        return self.phase_code == "3"
    
    @property
    def is_support_pole(self) -> bool:
        """지지주 여부"""
        return self.pole_type == "G"


@dataclass
class Line:
    """전선 데이터 클래스"""
    id: str                          # 전선 ID
    geometry: LineString             # 형상 (Shapely LineString)
    coords: List[Tuple[float, float]]  # 좌표 리스트
    line_type: Optional[str] = None  # 전선 타입 (H: 고압, L: 저압)
    phase_code: Optional[str] = None # 상 코드
    start_pole_id: Optional[str] = None  # 시작 전주 ID
    end_pole_id: Optional[str] = None    # 끝 전주 ID
    properties: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_high_voltage(self) -> bool:
        """고압 전선 여부"""
        # HV, H, 고압 등 다양한 형식 지원
        return self.line_type in ("H", "HV", "고압")
    
    @property
    def length(self) -> float:
        """전선 길이"""
        return self.geometry.length


@dataclass
class Road:
    """도로 데이터 클래스"""
    id: str                          # 도로 ID
    geometry: LineString             # 형상 (Shapely LineString)
    coords: List[Tuple[float, float]]  # 좌표 리스트
    road_type: Optional[str] = None  # 도로 타입
    properties: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def length(self) -> float:
        """도로 길이"""
        return self.geometry.length


@dataclass
class Building:
    """건물 데이터 클래스"""
    id: str                          # 건물 ID
    geometry: Polygon                # 형상 (Shapely Polygon)
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def contains_point(self, point: Point) -> bool:
        """점이 건물 내부에 있는지 확인"""
        return self.geometry.contains(point)


@dataclass
class ProcessedData:
    """전처리된 데이터 컨테이너 (지연 로딩 적용)"""
    poles: List[Pole] = field(default_factory=list)
    lines: List[Line] = field(default_factory=list)
    roads: List[Road] = field(default_factory=list)
    buildings: List[Building] = field(default_factory=list)
    
    # 통계
    raw_counts: Dict[str, int] = field(default_factory=dict)
    filtered_counts: Dict[str, int] = field(default_factory=dict)
    
    # 지연 로딩 캐시
    _building_union: Optional[Any] = field(default=None, repr=False)
    _high_voltage_poles: Optional[List[Pole]] = field(default=None, repr=False)
    _three_phase_poles: Optional[List[Pole]] = field(default=None, repr=False)
    
    @property
    def building_union(self):
        """건물 폴리곤 병합 (지연 로딩)"""
        if self._building_union is None and self.buildings:
            with profile_block("건물 병합"):
                self._building_union = unary_union([b.geometry for b in self.buildings])
        return self._building_union
    
    @property
    def high_voltage_poles(self) -> List[Pole]:
        """고압 전주 목록 (지연 로딩)"""
        if self._high_voltage_poles is None:
            self._high_voltage_poles = [p for p in self.poles if p.is_high_voltage]
        return self._high_voltage_poles
    
    @property
    def three_phase_poles(self) -> List[Pole]:
        """3상 전주 목록 (지연 로딩)"""
        if self._three_phase_poles is None:
            self._three_phase_poles = [p for p in self.poles if p.is_three_phase]
        return self._three_phase_poles
    
    def iter_poles_within_distance(
        self,
        center: Tuple[float, float],
        max_distance: float
    ) -> Iterator[Tuple[Pole, float]]:
        """
        거리 내 전주 제너레이터 (메모리 효율적)
        
        Args:
            center: 중심 좌표
            max_distance: 최대 거리
        
        Yields:
            (전주, 거리) 튜플
        """
        from app.utils.coordinate import calculate_distance
        
        for pole in self.poles:
            dist = calculate_distance(
                center[0], center[1],
                pole.coord[0], pole.coord[1]
            )
            if dist <= max_distance:
                yield pole, dist
    
    def clear_cache(self):
        """지연 로딩 캐시 초기화"""
        self._building_union = None
        self._high_voltage_poles = None
        self._three_phase_poles = None


class DataPreprocessor:
    """데이터 전처리기 (성능 최적화)"""
    
    def __init__(self):
        self.processed_data: Optional[ProcessedData] = None
    
    @profile
    def process(self, raw_data: Dict[str, List[Dict[str, Any]]]) -> ProcessedData:
        """
        WFS 원시 데이터를 전처리
        
        Args:
            raw_data: WFS에서 조회한 원시 데이터
                {
                    "poles": [...],
                    "lines": [...],
                    "transformers": [...],  # 변압기/인입선 (저압선 포함)
                    "roads": [...],
                    "buildings": [...]
                }
        
        Returns:
            전처리된 데이터
        """
        result = ProcessedData()
        
        # 원시 데이터 개수 기록
        result.raw_counts = {
            "poles": len(raw_data.get("poles", [])),
            "lines": len(raw_data.get("lines", [])),
            "transformers": len(raw_data.get("transformers", [])),
            "roads": len(raw_data.get("roads", [])),
            "buildings": len(raw_data.get("buildings", []))
        }
        
        # 각 레이어 전처리
        result.poles = self._process_poles(raw_data.get("poles", []))
        result.lines = self._process_lines(raw_data.get("lines", []))
        result.roads = self._process_roads(raw_data.get("roads", []))
        result.buildings = self._process_buildings(raw_data.get("buildings", []))
        
        # 변압기 레이어에서 저압선 추출 및 통합
        lv_lines = self._extract_lv_lines_from_transformers(raw_data.get("transformers", []))
        if lv_lines:
            logger.info(f"변압기 레이어에서 저압선 {len(lv_lines)}개 추출")
            result.lines.extend(lv_lines)
        
        # 필터링 후 개수 기록
        result.filtered_counts = {
            "poles": len(result.poles),
            "lines": len(result.lines),
            "lines_hv": len([l for l in result.lines if l.is_high_voltage]),
            "lines_lv": len([l for l in result.lines if not l.is_high_voltage]),
            "roads": len(result.roads),
            "buildings": len(result.buildings)
        }
        
        # 추가 정제: 건물/도로 내부 전주 제거
        result.poles = self._remove_poles_in_obstacles(
            result.poles, result.buildings, result.roads
        )
        result.filtered_counts["poles_final"] = len(result.poles)
        
        # 전선-전주 공간 연결 (연결 ID가 없는 경우)
        self._link_lines_to_poles(result.lines, result.poles)
        
        self.processed_data = result
        
        logger.info(f"데이터 전처리 완료: {result.filtered_counts}")
        
        return result
    
    def _process_poles(self, raw_poles: List[Dict[str, Any]]) -> List[Pole]:
        """
        전주 데이터 전처리
        - 철거 예정 전주 제외
        - 지지주(G타입) 제외
        
        WFS 필드 매핑:
        - GID: 전주 ID
        - POLE_FORM_CD: 전주 형태 코드 (O: 일반, G: 지지주)
        - FAC_STAT_CD: 시설 상태 코드 (EI: 사용, D: 삭제, R: 철거)
        """
        poles = []
        
        for feature in raw_poles:
            try:
                props = feature.get("properties", {})
                
                # 철거/삭제 상태 제외 (FAC_STAT_CD 확인)
                stat_cd = props.get("FAC_STAT_CD", "")
                if stat_cd in ["D", "R", "DD", "RR"]:
                    continue
                if props.get("REMOVE_YN") == "Y":
                    continue
                
                # 지지주 제외 (POLE_FORM_CD == 'G')
                pole_form_cd = props.get("POLE_FORM_CD", props.get("POLE_TYPE", ""))
                if pole_form_cd == "G":
                    continue
                
                # 지오메트리 파싱
                geom = feature.get("geometry")
                if not geom:
                    continue
                
                point = shape(geom)
                if not isinstance(point, Point):
                    continue
                
                # 전주 ID: GID 우선, 없으면 POLE_ID
                pole_id = str(props.get("GID", props.get("POLE_ID", props.get("FTR_IDN", id(feature)))))
                
                # 전주 타입 결정:
                # - POLE_KND_CD가 H로 시작하면 고압
                # - LINE_NO가 고압 선로 번호면 고압
                # - 기본적으로 배전 전주는 고압으로 간주
                pole_knd = props.get("POLE_KND_CD", "")
                pole_type = None  # 연결된 전선으로 고압/저압 판단
                
                # Pole 객체 생성
                pole = Pole(
                    id=pole_id,
                    geometry=point,
                    coord=(point.x, point.y),
                    pole_type=pole_type,
                    phase_code=None,  # 전주 자체에는 상 코드가 없음, 연결된 전선으로 판단
                    properties=props
                )
                poles.append(pole)
                
            except Exception as e:
                logger.warning(f"전주 파싱 오류: {e}")
                continue
        
        return poles
    
    def _process_lines(self, raw_lines: List[Dict[str, Any]]) -> List[Line]:
        """
        전선 데이터 전처리
        - 철거 예정 전선 제외
        
        WFS 필드 매핑:
        - GID: 전선 ID
        - PHAR_CLCD: 상 구분 코드 (CBA/ABC/RST = 3상, A/B/C/S = 단상)
        - LWER_FAC_GID: 시작 전주 GID
        - UPPO_FAC_GID: 끝 전주 GID
        - FAC_STAT_CD: 시설 상태 코드
        - PRWR_KND_CD: 전선 종류 (고압/저압 구분)
        """
        lines = []
        
        for feature in raw_lines:
            try:
                props = feature.get("properties", {})
                
                # 철거/삭제 상태 제외
                stat_cd = props.get("FAC_STAT_CD", "")
                if stat_cd in ["D", "R", "DD", "RR"]:
                    continue
                if props.get("REMOVE_YN") == "Y":
                    continue
                
                # 지오메트리 파싱
                geom = feature.get("geometry")
                if not geom:
                    continue
                
                line_geom = shape(geom)
                if not isinstance(line_geom, LineString):
                    continue
                
                # 전선 ID
                line_id = str(props.get("GID", props.get("LINE_ID", props.get("FTR_IDN", id(feature)))))
                
                # 상 코드 결정 (PHAR_CLCD)
                phar_clcd = props.get("PHAR_CLCD", "")
                if phar_clcd in ["CBA", "ABC", "RST", "3", "3P"]:
                    phase_code = "3"  # 3상
                elif phar_clcd and len(phar_clcd) >= 3:
                    phase_code = "3"  # 3개 이상의 문자면 3상
                else:
                    phase_code = "1"  # 그 외 단상
                
                # 전선 타입 결정 (고압/저압)
                # PRWR_KND_CD: 전선 종류 코드 (H: 고압, L: 저압)
                # VOLT_VAL: 전압값 (22900 = 고압, 220/380 = 저압)
                prwr_knd = props.get("PRWR_KND_CD", "")
                volt_val = props.get("VOLT_VAL", 0)
                
                # 저압 조건: 명시적으로 저압 표시되거나 전압이 1000V 미만
                if prwr_knd in ["LV", "L", "저압"]:
                    line_type = "LV"
                elif volt_val and float(volt_val) < 1000:
                    line_type = "LV"
                else:
                    # 기본값: 고압 (배전선로는 22.9kV가 기본)
                    line_type = "HV"
                
                # 연결된 전주 ID (GID 기반)
                start_pole_id = props.get("LWER_FAC_GID") or props.get("ST_POLE_ID") or props.get("FR_POLE_ID")
                end_pole_id = props.get("UPPO_FAC_GID") or props.get("ED_POLE_ID") or props.get("TO_POLE_ID")
                
                # 문자열 변환
                if start_pole_id:
                    start_pole_id = str(start_pole_id)
                if end_pole_id:
                    end_pole_id = str(end_pole_id)
                
                # Line 객체 생성
                line = Line(
                    id=line_id,
                    geometry=line_geom,
                    coords=list(line_geom.coords),
                    line_type=line_type,
                    phase_code=phase_code,
                    start_pole_id=start_pole_id,
                    end_pole_id=end_pole_id,
                    properties=props
                )
                lines.append(line)
                
            except Exception as e:
                logger.warning(f"전선 파싱 오류: {e}")
                continue
        
        return lines
    
    def _extract_lv_lines_from_transformers(
        self, 
        raw_transformers: List[Dict[str, Any]]
    ) -> List[Line]:
        """
        변압기/인입선 레이어에서 저압선 추출
        
        [데이터 구조]
        - 변압기 레이어(AI_FAC_003)에 저압선 정보가 포함되어 있음
        - TEXT_GIS_ANNXN 필드에서 "OW" (Outdoor Wire) 포함 시 저압선
        - 연결 전주 ID가 없으므로 공간 연결 필요
        
        WFS 필드 매핑:
        - GID: 전선 ID
        - TEXT_GIS_ANNXN: 전선 정보 (예: "OW 22 x 3")
        - PHAR_CLCD: 상 구분 코드
        - GIS_TRNSLN_PTH: 지오메트리 (인입선 경로)
        """
        lv_lines = []
        
        for feature in raw_transformers:
            try:
                props = feature.get("properties", {})
                
                # 철거/삭제 상태 제외
                stat_cd = props.get("FAC_STAT_CD", "")
                if stat_cd in ["D", "R", "DD", "RR"]:
                    continue
                
                # TEXT_GIS_ANNXN에서 저압선 여부 판단
                text_annxn = props.get("TEXT_GIS_ANNXN", "") or ""
                
                # OW (Outdoor Wire) 또는 WO가 포함되면 저압선
                # C4, AO 등은 인입선/케이블이므로 제외하거나 별도 처리
                is_lv_line = "OW" in text_annxn.upper() or "WO " in text_annxn.upper()
                
                if not is_lv_line:
                    continue
                
                # 지오메트리 파싱 (GIS_TRNSLN_PTH 사용)
                geom = feature.get("geometry")
                if not geom:
                    continue
                
                line_geom = shape(geom)
                if not isinstance(line_geom, LineString):
                    continue
                
                # 전선 ID
                line_id = str(props.get("GID", props.get("FTR_IDN", id(feature))))
                
                # 상 코드 결정
                phar_clcd = props.get("PHAR_CLCD", "")
                if phar_clcd in ["CBA", "ABC", "RST", "3", "3P"]:
                    phase_code = "3"
                elif phar_clcd and len(phar_clcd) >= 3:
                    phase_code = "3"
                else:
                    phase_code = "1"
                
                # 저압선으로 분류
                line_type = "LV"
                
                # 연결 전주 ID (변압기 레이어는 대부분 None)
                start_pole_id = props.get("LWER_FAC_GID") or props.get("ST_POLE_ID")
                end_pole_id = props.get("UPPO_FAC_GID") or props.get("ED_POLE_ID")
                
                if start_pole_id:
                    start_pole_id = str(start_pole_id)
                if end_pole_id:
                    end_pole_id = str(end_pole_id)
                
                # Line 객체 생성
                line = Line(
                    id=f"LV_{line_id}",  # ID 접두어로 저압선 구분
                    geometry=line_geom,
                    coords=list(line_geom.coords),
                    line_type=line_type,
                    phase_code=phase_code,
                    start_pole_id=start_pole_id,
                    end_pole_id=end_pole_id,
                    properties=props
                )
                lv_lines.append(line)
                
            except Exception as e:
                logger.warning(f"저압선 추출 오류: {e}")
                continue
        
        return lv_lines
    
    def _process_roads(self, raw_roads: List[Dict[str, Any]]) -> List[Road]:
        """
        도로 데이터 전처리
        """
        roads = []
        
        for feature in raw_roads:
            try:
                props = feature.get("properties", {})
                
                # 지오메트리 파싱
                geom = feature.get("geometry")
                if not geom:
                    continue
                
                road_geom = shape(geom)
                if not isinstance(road_geom, LineString):
                    continue
                
                # Road 객체 생성
                road = Road(
                    id=props.get("ROAD_ID", props.get("FTR_IDN", str(id(feature)))),
                    geometry=road_geom,
                    coords=list(road_geom.coords),
                    road_type=props.get("ROAD_TYPE", props.get("ROAD_TP")),
                    properties=props
                )
                roads.append(road)
                
            except Exception as e:
                logger.warning(f"도로 파싱 오류: {e}")
                continue
        
        return roads
    
    def _process_buildings(self, raw_buildings: List[Dict[str, Any]]) -> List[Building]:
        """
        건물 데이터 전처리
        """
        buildings = []
        
        for feature in raw_buildings:
            try:
                props = feature.get("properties", {})
                
                # 지오메트리 파싱
                geom = feature.get("geometry")
                if not geom:
                    continue
                
                building_geom = shape(geom)
                if not isinstance(building_geom, Polygon):
                    continue
                
                # Building 객체 생성
                building = Building(
                    id=props.get("BLDG_ID", props.get("FTR_IDN", str(id(feature)))),
                    geometry=building_geom,
                    properties=props
                )
                buildings.append(building)
                
            except Exception as e:
                logger.warning(f"건물 파싱 오류: {e}")
                continue
        
        return buildings
    
    def _remove_poles_in_obstacles(
        self,
        poles: List[Pole],
        buildings: List[Building],
        roads: List[Road]
    ) -> List[Pole]:
        """
        장애물(건물) 내부에 있는 전주 제거
        
        Note: 도로 위의 전주는 유지 (도로는 장애물이 아님)
        """
        if not buildings:
            return poles
        
        # 건물 폴리곤 병합 (성능 최적화)
        building_union = unary_union([b.geometry for b in buildings])
        
        filtered_poles = []
        for pole in poles:
            # 건물 내부에 있는지 확인
            if not building_union.contains(pole.geometry):
                filtered_poles.append(pole)
            else:
                logger.debug(f"건물 내부 전주 제외: {pole.id}")
        
        return filtered_poles
    
    def get_high_voltage_poles(self) -> List[Pole]:
        """고압 전주만 반환"""
        if not self.processed_data:
            return []
        return [p for p in self.processed_data.poles if p.is_high_voltage]
    
    def get_three_phase_poles(self) -> List[Pole]:
        """3상 전주만 반환"""
        if not self.processed_data:
            return []
        return [p for p in self.processed_data.poles if p.is_three_phase]
    
    def get_poles_connected_to_hv_line(self) -> List[Pole]:
        """
        고압선에 연결된 전주만 반환
        (전선 데이터의 start_pole_id, end_pole_id 활용)
        """
        if not self.processed_data:
            return []
        
        # 고압선에 연결된 전주 ID 수집
        hv_pole_ids = set()
        for line in self.processed_data.lines:
            if line.is_high_voltage:
                if line.start_pole_id:
                    hv_pole_ids.add(line.start_pole_id)
                if line.end_pole_id:
                    hv_pole_ids.add(line.end_pole_id)
        
        # 해당 전주 반환
        return [p for p in self.processed_data.poles if p.id in hv_pole_ids]
    
    def _link_lines_to_poles(
        self,
        lines: List[Line],
        poles: List[Pole],
        max_distance: float = 15.0
    ):
        """
        전선-전주 공간 연결 (연결 ID가 없는 경우)
        
        전선의 시작점/끝점과 가장 가까운 전주를 찾아 연결 관계 설정
        - 저압선(LV)은 변압기 레이어에서 추출되어 연결 ID가 없음
        - 공간 분석으로 전주 연결 관계 구축
        
        Args:
            lines: 전선 리스트
            poles: 전주 리스트  
            max_distance: 연결 판정 최대 거리 (미터, 기본 15m)
        """
        from app.utils.coordinate import calculate_distance
        
        if not poles:
            return
        
        # 전주 좌표 맵 생성
        pole_coords = [(p.id, p.coord) for p in poles]
        
        linked_count = 0
        
        for line in lines:
            # 이미 연결 ID가 있으면 스킵
            if line.start_pole_id and line.end_pole_id:
                continue
            
            if not line.coords or len(line.coords) < 2:
                continue
            
            # 전선의 시작점과 끝점
            start_coord = line.coords[0]
            end_coord = line.coords[-1]
            
            # 시작점에서 가장 가까운 전주 찾기
            if not line.start_pole_id:
                min_dist = float('inf')
                nearest_pole_id = None
                for pole_id, pole_coord in pole_coords:
                    dist = calculate_distance(
                        start_coord[0], start_coord[1],
                        pole_coord[0], pole_coord[1]
                    )
                    if dist < min_dist and dist <= max_distance:
                        min_dist = dist
                        nearest_pole_id = pole_id
                
                if nearest_pole_id:
                    line.start_pole_id = nearest_pole_id
                    linked_count += 1
            
            # 끝점에서 가장 가까운 전주 찾기
            if not line.end_pole_id:
                min_dist = float('inf')
                nearest_pole_id = None
                for pole_id, pole_coord in pole_coords:
                    dist = calculate_distance(
                        end_coord[0], end_coord[1],
                        pole_coord[0], pole_coord[1]
                    )
                    if dist < min_dist and dist <= max_distance:
                        min_dist = dist
                        nearest_pole_id = pole_id
                
                if nearest_pole_id:
                    line.end_pole_id = nearest_pole_id
                    linked_count += 1
        
        if linked_count > 0:
            logger.info(f"전선-전주 공간 연결: {linked_count}개 연결 생성")