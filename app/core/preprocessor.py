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
import re

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
    voltage: Optional[float] = None  # [NEW] 실제 전압값 (V) - DB의 VOLT_VAL
    has_transformer: bool = False    # [NEW] 변압기 보유 여부 (공간 매핑 결과)
    properties: Dict[str, Any] = field(default_factory=dict)  # 기타 속성
    
    @property
    def is_high_voltage(self) -> bool:
        """고압 전주 여부"""
        # voltage 값이 있으면 우선 판단
        if self.voltage is not None:
            return self.voltage >= 1000
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
    wire_spec: Optional[str] = None  # [NEW] 전선 규격 (예: ACSR_160, OW_22)
    voltage: Optional[float] = None  # [NEW] 실제 전압값 (V)
    start_pole_id: Optional[str] = None  # 시작 전주 ID
    end_pole_id: Optional[str] = None    # 끝 전주 ID
    is_obstacle: bool = True         # 교차 검증 대상 여부
    is_service_drop: bool = False    # 인입선 여부 (교차 허용 대상)
    properties: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_high_voltage(self) -> bool:
        """고압 전선 여부"""
        if self.voltage is not None:
            return self.voltage >= 1000
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
class Transformer:
    """변압기 데이터 클래스"""
    id: str
    geometry: Point
    coord: Tuple[float, float]
    capacity_kva: float = 0.0
    phase_code: str = "1"
    pole_id: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessedData:
    """전처리된 데이터 컨테이너 (지연 로딩 적용)"""
    poles: List[Pole] = field(default_factory=list)
    lines: List[Line] = field(default_factory=list)
    transformers: List[Transformer] = field(default_factory=list)  # [NEW]
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


# [GLOBAL CACHE] 전주 계통 분석 결과 메모리 상주 (최대 1GB 내외 활용 가능)
# 구조: { pole_id: {"type": "H", "phase": "3"} }
_POLE_INTELLIGENCE_CACHE: Dict[str, Dict[str, str]] = {}

class DataPreprocessor:
    """데이터 전처리기 (성능 및 메모리 최적화)"""
    
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
                    "lines_hv": [...],
                    "lines_lv": [...],
                    "transformers": [...],
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
            "lines_hv": len(raw_data.get("lines_hv", [])),
            "lines_lv": len(raw_data.get("lines_lv", [])),
            "transformers": len(raw_data.get("transformers", [])),
            "roads": len(raw_data.get("roads", [])),
            "buildings": len(raw_data.get("buildings", []))
        }
        
        # 각 레이어 전처리
        result.poles = self._process_poles(raw_data.get("poles", []))
        
        # 전선 처리 (HV/LV 분리)
        hv_lines = self._process_hv_lines(raw_data.get("lines_hv", []))
        lv_lines = self._process_lv_lines(raw_data.get("lines_lv", []))
        result.lines = hv_lines + lv_lines
        
        # 변압기 처리
        result.transformers = self._process_transformers(raw_data.get("transformers", []))
        
        result.roads = self._process_roads(raw_data.get("roads", []))
        result.buildings = self._process_buildings(raw_data.get("buildings", []))
        
        # 필터링 후 개수 기록
        result.filtered_counts = {
            "poles": len(result.poles),
            "lines": len(result.lines),
            "lines_hv": len(hv_lines),
            "lines_lv": len(lv_lines),
            "transformers": len(result.transformers),
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
        
        # [NEW] 변압기-전주 공간 연결 (ID 링크 부재 대응)
        self._link_transformers_to_poles(result.transformers, result.poles)
        
        # [NEW] 반경 2.5m 공간 분석을 통한 전주 계통 정보(HV/LV/상) 복원
        self._enrich_pole_data_spatially(result.poles, result.lines, radius=2.5)
        
        self.processed_data = result
        
        logger.info(f"데이터 전처리 완료: {result.filtered_counts}")
        
        return result

    def _enrich_pole_data_spatially(self, poles: List[Pole], lines: List[Line], radius: float = 2.5):
        """
        [최적화] 글로벌 캐시 및 공간 인덱스를 사용하여 전주 계통 정보를 초고속으로 복원합니다.
        """
        if not poles or not lines:
            return

        from shapely.strtree import STRtree
        
        # 1. 캐시에 없는 전주들만 선별
        poles_to_analyze = [p for p in poles if p.id not in _POLE_INTELLIGENCE_CACHE]
        
        # 모든 전주에 대해 캐시 데이터 우선 적용
        for p in poles:
            if p.id in _POLE_INTELLIGENCE_CACHE:
                cached = _POLE_INTELLIGENCE_CACHE[p.id]
                p.pole_type = cached["type"]
                p.phase_code = cached["phase"]

        if not poles_to_analyze:
            return

        # 2. 신규 전주들에 대해서만 공간 분석 수행
        line_geoms = [l.geometry for l in lines]
        tree = STRtree(line_geoms)
        
        enriched_count = 0
        for pole in poles_to_analyze:
            nearby_indices = tree.query(pole.geometry.buffer(radius))
            
            nearby_hv = False
            nearby_3phase = False
            nearby_lv = False
            
            for idx in nearby_indices:
                line = lines[idx]
                if line.line_type == "HV": nearby_hv = True
                else: nearby_lv = True
                if line.phase_code == "3": nearby_3phase = True
            
            # 최종 타입 결정
            p_type = "H" if nearby_hv else "L"
            p_phase = "3" if nearby_3phase else "1"
            
            # 전주 객체 및 글로벌 캐시 업데이트
            pole.pole_type = p_type
            pole.phase_code = p_phase
            _POLE_INTELLIGENCE_CACHE[pole.id] = {"type": p_type, "phase": p_phase}
            enriched_count += 1
                
        logger.info(f"메모리 캐시 가속 적용: 신규 분석 {enriched_count}개, 캐시 활용 {len(poles) - enriched_count}개")
    
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
                
                # [NEW] 전압값 파싱 (전주 레이어에는 드물게 존재할 수 있음)
                volt_val = props.get("VOLT_VAL")
                voltage = None
                if volt_val and str(volt_val).isdigit() and int(volt_val) > 0:
                    voltage = float(volt_val)
                
                # Pole 객체 생성
                pole = Pole(
                    id=pole_id,
                    geometry=point,
                    coord=(point.x, point.y),
                    pole_type=pole_type,
                    phase_code=None,  # 전주 자체에는 상 코드가 없음, 연결된 전선으로 판단
                    voltage=voltage,  # [NEW]
                    properties=props
                )
                poles.append(pole)
                
            except Exception as e:
                logger.warning(f"전주 파싱 오류: {e}")
                continue
        
        return poles
    
    def _process_hv_lines(self, raw_lines: List[Dict[str, Any]]) -> List[Line]:
        """
        고압전선 데이터 전처리 (AI_FAC_002)
        - 무조건 HV 타입
        - 3상/단상 구분
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
                
                # 상 코드 결정 (PHAR_CLCD) - 매핑 테이블 활용
                phar_clcd = str(props.get("PHAR_CLCD", "")).strip().upper()
                phase_code = settings.PHASE_MAPPING.get(phar_clcd, "1")
                
                # 전선 규격 파싱
                prwr_spec = str(props.get("PRWR_SPEC_CD", "")).strip()
                wire_spec = settings.WIRE_SPEC_MAPPING.get(prwr_spec)
                
                # 전압값 파싱
                volt_val = props.get("VOLT_VAL")
                voltage = None
                if volt_val and str(volt_val).isdigit() and int(volt_val) > 0:
                    voltage = float(volt_val)

                # 연결된 전주 ID
                start_pole_id = props.get("LWER_FAC_GID") or props.get("ST_POLE_ID") or props.get("FR_POLE_ID")
                end_pole_id = props.get("UPPO_FAC_GID") or props.get("ED_POLE_ID") or props.get("TO_POLE_ID")
                
                if start_pole_id: start_pole_id = str(start_pole_id)
                if end_pole_id: end_pole_id = str(end_pole_id)
                
                # Line 객체 생성 (HV 고정, 장애물 고정)
                line = Line(
                    id=line_id,
                    geometry=line_geom,
                    coords=list(line_geom.coords),
                    line_type="HV",
                    phase_code=phase_code,
                    wire_spec=wire_spec,
                    voltage=voltage,
                    start_pole_id=start_pole_id,
                    end_pole_id=end_pole_id,
                    is_obstacle=True,  # 고압선은 무조건 장애물
                    is_service_drop=False,
                    properties=props
                )
                lines.append(line)
                
            except Exception as e:
                logger.warning(f"고압전선 파싱 오류: {e}")
                continue
        
        return lines
    
    def _process_lv_lines(self, raw_lines: List[Dict[str, Any]]) -> List[Line]:
        """
        저압전선 데이터 전처리 (AI_FAC_003)
        - 무조건 LV 타입
        - 인입선(DV) 여부 식별 -> 장애물 제외
        """
        lines = []
        
        for feature in raw_lines:
            try:
                props = feature.get("properties", {})
                
                # 철거/삭제 상태 제외
                stat_cd = props.get("FAC_STAT_CD", "")
                if stat_cd in ["D", "R", "DD", "RR"]:
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
                
                # 상 코드 결정
                phar_clcd = str(props.get("PHAR_CLCD", "")).strip().upper()
                phase_code = settings.PHASE_MAPPING.get(phar_clcd, "1")
                
                # 인입선 여부 판별 (PRWR_KND_CD or TEXT_GIS_ANNXN)
                prwr_knd = str(props.get("PRWR_KND_CD", "")).upper()
                text_annxn = str(props.get("TEXT_GIS_ANNXN", "")).upper()
                
                is_service_drop = False
                if "DV" in prwr_knd or "인입" in prwr_knd or "DV" in text_annxn:
                    is_service_drop = True
                
                # 장애물 여부: 인입선이면 False, 본선(OW)이면 True
                is_obstacle = not is_service_drop
                
                # 연결 전주 ID
                start_pole_id = props.get("LWER_FAC_GID")
                end_pole_id = props.get("UPPO_FAC_GID")
                
                if start_pole_id: start_pole_id = str(start_pole_id)
                if end_pole_id: end_pole_id = str(end_pole_id)

                # 전선 규격
                prwr_spec = str(props.get("PRWR_SPEC_CD", "")).strip()
                wire_spec = settings.WIRE_SPEC_MAPPING.get(prwr_spec)

                line = Line(
                    id=line_id,
                    geometry=line_geom,
                    coords=list(line_geom.coords),
                    line_type="LV",
                    phase_code=phase_code,
                    wire_spec=wire_spec,
                    voltage=380.0 if phase_code == "3" else 220.0, # 저압 표준전압
                    start_pole_id=start_pole_id,
                    end_pole_id=end_pole_id,
                    is_obstacle=is_obstacle,
                    is_service_drop=is_service_drop,
                    properties=props
                )
                lines.append(line)
                
            except Exception as e:
                logger.warning(f"저압전선 파싱 오류: {e}")
                continue
        
        return lines

    def _parse_transformer_capacity(self, text_annxn: str) -> float:
        """
        TEXT_GIS_ANNXN 필드에서 변압기 용량 추출
        예: '30X1|20X2' -> 30*1 + 20*2 = 70.0
        """
        if not text_annxn:
            return 0.0
        
        total_kva = 0.0
        # 패턴: (숫자)X(개수)
        matches = re.findall(r'(\d+)X(\d+)', text_annxn.upper())
        for cap, count in matches:
            try:
                total_kva += float(cap) * float(count)
            except ValueError:
                continue
        return total_kva

    def _process_transformers(self, raw_trs: List[Dict[str, Any]]) -> List[Transformer]:
        """
        변압기 데이터 전처리 (AI_FAC_004)
        """
        transformers = []
        
        for feature in raw_trs:
            try:
                props = feature.get("properties", {})
                
                # 철거 제외
                stat_cd = props.get("FAC_STAT_CD", "")
                if stat_cd in ["D", "R", "DD", "RR"]:
                    continue
                
                geom = feature.get("geometry")
                if not geom: continue
                
                point = shape(geom)
                if not isinstance(point, Point): continue
                
                tr_id = str(props.get("GID", id(feature)))
                
                # 용량 파싱 (TEXT_GIS_ANNXN 우선, 없으면 CAP_KVA)
                text_annxn = props.get("TEXT_GIS_ANNXN", "")
                cap_kva = self._parse_transformer_capacity(text_annxn)
                
                if cap_kva == 0.0:
                    val = props.get("CAP_KVA") or props.get("KVA")
                    if val:
                        try: cap_kva = float(val)
                        except: pass
                
                # 상 정보
                phar_clcd = str(props.get("PHAR_CLCD", "")).strip().upper()
                phase_code = settings.PHASE_MAPPING.get(phar_clcd, "1")
                
                tr = Transformer(
                    id=tr_id,
                    geometry=point,
                    coord=(point.x, point.y),
                    capacity_kva=cap_kva,
                    phase_code=phase_code,
                    properties=props
                )
                transformers.append(tr)
                
            except Exception as e:
                logger.warning(f"변압기 파싱 오류: {e}")
                continue
        
        return transformers
    
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

    def _link_transformers_to_poles(
        self,
        transformers: List[Transformer],
        poles: List[Pole],
        max_distance: Optional[float] = None
    ):
        """
        변압기-전주 공간 연결 (Snapping)
        ID 링크가 없는 경우 좌표 기반으로 가장 가까운 전주에 변압기 할당
        """
        from app.utils.coordinate import calculate_distance
        
        if not transformers or not poles:
            return
            
        snap_dist = max_distance or settings.TRANSFORMER_SNAP_DISTANCE
        linked_count = 0
        
        # 전주 좌표 맵 생성
        pole_coords = [(p.id, p.coord, p) for p in poles]
        
        for tr in transformers:
            # 이미 pole_id가 있으면 스킵 (거의 없겠지만)
            if tr.pole_id:
                continue
                
            min_dist = float('inf')
            nearest_pole = None
            
            for p_id, p_coord, p_obj in pole_coords:
                dist = calculate_distance(
                    tr.coord[0], tr.coord[1],
                    p_coord[0], p_coord[1]
                )
                if dist < min_dist and dist <= snap_dist:
                    min_dist = dist
                    nearest_pole = p_obj
            
            if nearest_pole:
                tr.pole_id = nearest_pole.id
                nearest_pole.has_transformer = True
                linked_count += 1
                
        if linked_count > 0:
            logger.info(f"변압기-전주 공간 연결: {linked_count}개 매핑 완료 (범위: {snap_dist}m)")