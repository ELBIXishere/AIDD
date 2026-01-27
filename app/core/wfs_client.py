"""
ELBIX AIDD WFS 클라이언트
- GetFeature 요청을 통한 GIS 데이터 수집
- 비동기 HTTP 클라이언트 사용
- 연결 풀링 및 응답 캐싱 적용
"""

import httpx
import aiohttp
from typing import List, Dict, Any, Optional, Tuple, ClassVar
from dataclasses import dataclass
import json
import logging
import hashlib
import threading
from cachetools import TTLCache

from app.config import settings
from app.utils.coordinate import calculate_bbox
from app.utils.profiler import profile_async

logger = logging.getLogger(__name__)


class WFSCache:
    """
    WFS 응답 캐싱 (Thread-safe)
    
    - TTL 기반 캐시 (기본 5분)
    - 좌표 기반 캐시 키 생성
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    # maxsize=100, ttl=300초 (5분)
                    cls._instance._cache = TTLCache(maxsize=100, ttl=300)
                    cls._instance._hits = 0
                    cls._instance._misses = 0
        return cls._instance
    
    @classmethod
    def generate_key(cls, url: str, bbox: Tuple[float, float, float, float], layer: str) -> str:
        """캐시 키 생성 (BBox 좌표를 정수로 반올림하여 키 생성)"""
        # 좌표를 미터 단위로 반올림 (10m 단위)
        rounded_bbox = tuple(round(c / 10) * 10 for c in bbox)
        key_str = f"{url}:{layer}:{rounded_bbox}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[List[Dict[str, Any]]]:
        """캐시에서 데이터 조회"""
        with self._lock:
            result = self._cache.get(key)
            if result is not None:
                self._hits += 1
                logger.debug(f"[Cache HIT] key={key[:8]}...")
            else:
                self._misses += 1
            return result
    
    def set(self, key: str, data: List[Dict[str, Any]]):
        """캐시에 데이터 저장"""
        with self._lock:
            self._cache[key] = data
            logger.debug(f"[Cache SET] key={key[:8]}..., items={len(data)}")
    
    def clear(self):
        """캐시 초기화"""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    @property
    def stats(self) -> Dict[str, Any]:
        """캐시 통계"""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "size": len(self._cache)
        }


class WFSConnectionPool:
    """
    WFS 연결 풀 관리 (Singleton)
    
    - aiohttp ClientSession 재사용
    - TCPConnector로 연결 수 제한
    """
    
    _instance = None
    _lock = threading.Lock()
    _session: Optional[aiohttp.ClientSession] = None
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    async def get_session(cls) -> aiohttp.ClientSession:
        """공유 세션 반환 (없으면 생성)"""
        if cls._session is None or cls._session.closed:
            connector = aiohttp.TCPConnector(
                limit=10,              # 최대 동시 연결 수
                limit_per_host=5,      # 호스트당 최대 연결 수
                keepalive_timeout=30,  # Keep-alive 타임아웃
                enable_cleanup_closed=True
            )
            timeout = aiohttp.ClientTimeout(total=settings.HTTP_TIMEOUT)
            cls._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
            logger.info("WFS 연결 풀 생성: limit=10, keepalive=30s")
        return cls._session
    
    @classmethod
    async def close(cls):
        """세션 종료"""
        if cls._session and not cls._session.closed:
            await cls._session.close()
            cls._session = None
            logger.info("WFS 연결 풀 종료")


# 전역 캐시 인스턴스
_wfs_cache = WFSCache()


@dataclass
class WFSLayer:
    """WFS 레이어 정보"""
    name: str           # 레이어명
    geometry_field: str  # 지오메트리 필드명
    wfs_url: str        # WFS 서버 URL


# 레이어 정의
GIS_LAYERS = {
    "pole": WFSLayer(
        name=settings.LAYER_POLE,
        geometry_field=settings.GEOM_POLE,
        wfs_url=settings.GIS_WFS_URL
    ),
    "line": WFSLayer(
        name=settings.LAYER_LINE,
        geometry_field=settings.GEOM_LINE,
        wfs_url=settings.GIS_WFS_URL
    ),
    "transformer": WFSLayer(
        name=settings.LAYER_TRANSFORMER,
        geometry_field=settings.GEOM_TRANSFORMER,
        wfs_url=settings.GIS_WFS_URL
    ),
}

BASE_LAYERS = {
    "road": WFSLayer(
        name=settings.LAYER_ROAD,
        geometry_field=settings.GEOM_ROAD,
        wfs_url=settings.BASE_WFS_URL
    ),
    "building": WFSLayer(
        name=settings.LAYER_BUILDING,
        geometry_field=settings.GEOM_BUILDING,
        wfs_url=settings.BASE_WFS_URL
    ),
    "railway": WFSLayer(
        name=settings.LAYER_RAILWAY,
        geometry_field=settings.GEOM_RAILWAY,
        wfs_url=settings.BASE_WFS_URL
    ),
    "river": WFSLayer(
        name=settings.LAYER_RIVER,
        geometry_field=settings.GEOM_RIVER,
        wfs_url=settings.BASE_WFS_URL
    ),
}


def build_getfeature_xml(
    layer_name: str,
    geometry_field: str,
    bbox: Tuple[float, float, float, float],
    srs_name: str = "EPSG:3857",
    max_features: int = 1000
) -> str:
    """
    WFS GetFeature 요청 XML 생성
    
    Args:
        layer_name: 레이어명
        geometry_field: 지오메트리 필드명
        bbox: BBox (min_x, min_y, max_x, max_y)
        srs_name: 좌표계
        max_features: 최대 피처 수
    
    Returns:
        GetFeature 요청 XML 문자열
    """
    min_x, min_y, max_x, max_y = bbox
    
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<wfs:GetFeature
    service="WFS"
    version="1.1.0"
    maxFeatures="{max_features}"
    outputFormat="application/json"
    xmlns:wfs="http://www.opengis.net/wfs"
    xmlns:ogc="http://www.opengis.net/ogc"
    xmlns:gml="http://www.opengis.net/gml">
    <wfs:Query typeName="{layer_name}" srsName="{srs_name}">
        <ogc:Filter>
            <ogc:BBOX>
                <ogc:PropertyName>{geometry_field}</ogc:PropertyName>
                <gml:Envelope srsName="{srs_name}">
                    <gml:lowerCorner>{min_x} {min_y}</gml:lowerCorner>
                    <gml:upperCorner>{max_x} {max_y}</gml:upperCorner>
                </gml:Envelope>
            </ogc:BBOX>
        </ogc:Filter>
    </wfs:Query>
</wfs:GetFeature>'''
    
    return xml


def build_getfeature_xml_with_filter(
    layer_name: str,
    geometry_field: str,
    bbox: Tuple[float, float, float, float],
    property_filters: Dict[str, Any] = None,
    srs_name: str = "EPSG:3857",
    max_features: int = 1000
) -> str:
    """
    필터 조건이 포함된 WFS GetFeature 요청 XML 생성
    
    Args:
        layer_name: 레이어명
        geometry_field: 지오메트리 필드명
        bbox: BBox
        property_filters: 속성 필터 조건 (예: {"POLE_TYPE": "H"})
        srs_name: 좌표계
        max_features: 최대 피처 수
    
    Returns:
        GetFeature 요청 XML 문자열
    """
    min_x, min_y, max_x, max_y = bbox
    
    # 필터 조건 생성
    filter_conditions = []
    
    # BBox 필터
    bbox_filter = f'''<ogc:BBOX>
                <ogc:PropertyName>{geometry_field}</ogc:PropertyName>
                <gml:Envelope srsName="{srs_name}">
                    <gml:lowerCorner>{min_x} {min_y}</gml:lowerCorner>
                    <gml:upperCorner>{max_x} {max_y}</gml:upperCorner>
                </gml:Envelope>
            </ogc:BBOX>'''
    filter_conditions.append(bbox_filter)
    
    # 속성 필터
    if property_filters:
        for prop_name, prop_value in property_filters.items():
            if isinstance(prop_value, list):
                # OR 조건
                or_filters = [
                    f'<ogc:PropertyIsEqualTo><ogc:PropertyName>{prop_name}</ogc:PropertyName><ogc:Literal>{v}</ogc:Literal></ogc:PropertyIsEqualTo>'
                    for v in prop_value
                ]
                filter_conditions.append(f'<ogc:Or>{"".join(or_filters)}</ogc:Or>')
            else:
                filter_conditions.append(
                    f'<ogc:PropertyIsEqualTo><ogc:PropertyName>{prop_name}</ogc:PropertyName><ogc:Literal>{prop_value}</ogc:Literal></ogc:PropertyIsEqualTo>'
                )
    
    # 필터 조합
    if len(filter_conditions) == 1:
        filter_xml = filter_conditions[0]
    else:
        filter_xml = f'<ogc:And>{"".join(filter_conditions)}</ogc:And>'
    
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<wfs:GetFeature
    service="WFS"
    version="1.1.0"
    maxFeatures="{max_features}"
    outputFormat="application/json"
    xmlns:wfs="http://www.opengis.net/wfs"
    xmlns:ogc="http://www.opengis.net/ogc"
    xmlns:gml="http://www.opengis.net/gml">
    <wfs:Query typeName="{layer_name}" srsName="{srs_name}">
        <ogc:Filter>
            {filter_xml}
        </ogc:Filter>
    </wfs:Query>
</wfs:GetFeature>'''
    
    return xml


class WFSClient:
    """WFS 데이터 수집 클라이언트 (연결 풀링 + 캐싱)"""
    
    def __init__(
        self,
        gis_wfs_url: str = None,
        base_wfs_url: str = None,
        timeout: float = None,
        use_cache: bool = True
    ):
        """
        WFS 클라이언트 초기화
        
        Args:
            gis_wfs_url: GIS WFS 서버 URL
            base_wfs_url: BASE WFS 서버 URL
            timeout: HTTP 타임아웃 (초)
            use_cache: 캐싱 사용 여부
        """
        self.gis_wfs_url = gis_wfs_url or settings.GIS_WFS_URL
        self.base_wfs_url = base_wfs_url or settings.BASE_WFS_URL
        self.timeout = timeout or settings.HTTP_TIMEOUT
        self.use_cache = use_cache
        self.cache = _wfs_cache
    
    @profile_async
    async def _fetch_features(
        self,
        url: str,
        xml_body: str,
        cache_key: str = None
    ) -> List[Dict[str, Any]]:
        """
        WFS GetFeature 요청 실행 (연결 풀 + 캐싱)
        
        Args:
            url: WFS 서버 URL
            xml_body: GetFeature 요청 XML
            cache_key: 캐시 키 (제공 시 캐싱 활성화)
        
        Returns:
            피처 리스트
        """
        # 캐시 확인
        if cache_key and self.use_cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached
        
        headers = {
            "Content-Type": "text/xml",
            "Accept": "application/json",
        }
        
        try:
            # 연결 풀에서 세션 가져오기
            session = await WFSConnectionPool.get_session()
            
            async with session.post(url, data=xml_body, headers=headers) as response:
                response.raise_for_status()
                text = await response.text()
                
                # JSON 파싱 시도
                if text.strip().startswith('{') or text.strip().startswith('['):
                    data = json.loads(text)
                    
                    # GeoJSON FeatureCollection 형식 파싱
                    if isinstance(data, dict) and "features" in data:
                        result = data["features"]
                    elif isinstance(data, list):
                        result = data
                    else:
                        result = []
                    
                    # 캐시에 저장
                    if cache_key and self.use_cache:
                        self.cache.set(cache_key, result)
                    
                    return result
                else:
                    # XML 응답일 수 있음 - 빈 리스트 반환
                    logger.warning(f"WFS 응답이 JSON 형식이 아닙니다: {text[:200]}")
                    return []
                    
        except aiohttp.ClientResponseError as e:
            logger.error(f"WFS HTTP 오류: {e}")
            raise
        except Exception as e:
            logger.error(f"WFS 요청 오류: {e}")
            raise
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        return self.cache.stats
    
    def clear_cache(self):
        """캐시 초기화"""
        self.cache.clear()
    
    @classmethod
    async def close_pool(cls):
        """연결 풀 종료"""
        await WFSConnectionPool.close()
    
    @profile_async
    async def get_poles(
        self,
        center_x: float,
        center_y: float,
        bbox_size: float = None
    ) -> List[Dict[str, Any]]:
        """
        전주 데이터 조회 (캐싱 적용)
        
        Args:
            center_x, center_y: 중심 좌표 (EPSG:3857)
            bbox_size: BBox 크기 (미터)
        
        Returns:
            전주 피처 리스트
        """
        bbox = calculate_bbox(center_x, center_y, bbox_size or settings.BBOX_SIZE)
        layer = GIS_LAYERS["pole"]
        
        # 캐시 키 생성
        cache_key = WFSCache.generate_key(self.gis_wfs_url, bbox, "pole")
        
        xml = build_getfeature_xml(
            layer_name=layer.name,
            geometry_field=layer.geometry_field,
            bbox=bbox
        )
        
        return await self._fetch_features(self.gis_wfs_url, xml, cache_key)
    
    @profile_async
    async def get_lines(
        self,
        center_x: float,
        center_y: float,
        bbox_size: float = None
    ) -> List[Dict[str, Any]]:
        """
        전선 데이터 조회 (캐싱 적용)
        
        Args:
            center_x, center_y: 중심 좌표 (EPSG:3857)
            bbox_size: BBox 크기 (미터)
        
        Returns:
            전선 피처 리스트
        """
        bbox = calculate_bbox(center_x, center_y, bbox_size or settings.BBOX_SIZE)
        layer = GIS_LAYERS["line"]
        
        cache_key = WFSCache.generate_key(self.gis_wfs_url, bbox, "line")
        
        xml = build_getfeature_xml(
            layer_name=layer.name,
            geometry_field=layer.geometry_field,
            bbox=bbox
        )
        
        return await self._fetch_features(self.gis_wfs_url, xml, cache_key)
    
    @profile_async
    async def get_roads(
        self,
        center_x: float,
        center_y: float,
        bbox_size: float = None
    ) -> List[Dict[str, Any]]:
        """
        도로 데이터 조회 (캐싱 적용)
        
        Args:
            center_x, center_y: 중심 좌표 (EPSG:3857)
            bbox_size: BBox 크기 (미터)
        
        Returns:
            도로 피처 리스트
        """
        bbox = calculate_bbox(center_x, center_y, bbox_size or settings.BBOX_SIZE)
        layer = BASE_LAYERS["road"]
        
        cache_key = WFSCache.generate_key(self.base_wfs_url, bbox, "road")
        
        xml = build_getfeature_xml(
            layer_name=layer.name,
            geometry_field=layer.geometry_field,
            bbox=bbox
        )
        
        return await self._fetch_features(self.base_wfs_url, xml, cache_key)
    
    @profile_async
    async def get_buildings(
        self,
        center_x: float,
        center_y: float,
        bbox_size: float = None
    ) -> List[Dict[str, Any]]:
        """
        건물 데이터 조회 (캐싱 적용)
        
        Args:
            center_x, center_y: 중심 좌표 (EPSG:3857)
            bbox_size: BBox 크기 (미터)
        
        Returns:
            건물 피처 리스트
        """
        bbox = calculate_bbox(center_x, center_y, bbox_size or settings.BBOX_SIZE)
        layer = BASE_LAYERS["building"]
        
        cache_key = WFSCache.generate_key(self.base_wfs_url, bbox, "building")
        
        xml = build_getfeature_xml(
            layer_name=layer.name,
            geometry_field=layer.geometry_field,
            bbox=bbox
        )
        
        return await self._fetch_features(self.base_wfs_url, xml, cache_key)
    
    @profile_async
    async def get_transformers(
        self,
        center_x: float,
        center_y: float,
        bbox_size: float = None,
        max_features: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        변압기 데이터 조회 (캐싱 적용)
        
        Args:
            center_x, center_y: 중심 좌표 (EPSG:3857)
            bbox_size: BBox 크기 (미터)
            max_features: 최대 피처 수
        
        Returns:
            변압기 피처 리스트
        """
        bbox = calculate_bbox(center_x, center_y, bbox_size or settings.BBOX_SIZE)
        layer = GIS_LAYERS["transformer"]
        
        cache_key = WFSCache.generate_key(self.gis_wfs_url, bbox, "transformer")
        
        xml = build_getfeature_xml(
            layer_name=layer.name,
            geometry_field=layer.geometry_field,
            bbox=bbox,
            max_features=max_features
        )
        
        return await self._fetch_features(self.gis_wfs_url, xml, cache_key)
    
    @profile_async
    async def get_railways(
        self,
        center_x: float,
        center_y: float,
        bbox_size: float = None,
        max_features: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        철도 데이터 조회 (캐싱 적용)
        
        Args:
            center_x, center_y: 중심 좌표 (EPSG:3857)
            bbox_size: BBox 크기 (미터)
            max_features: 최대 피처 수
        
        Returns:
            철도 피처 리스트
        """
        bbox = calculate_bbox(center_x, center_y, bbox_size or settings.BBOX_SIZE)
        layer = BASE_LAYERS["railway"]
        
        cache_key = WFSCache.generate_key(self.base_wfs_url, bbox, "railway")
        
        xml = build_getfeature_xml(
            layer_name=layer.name,
            geometry_field=layer.geometry_field,
            bbox=bbox,
            max_features=max_features
        )
        
        return await self._fetch_features(self.base_wfs_url, xml, cache_key)
    
    @profile_async
    async def get_rivers(
        self,
        center_x: float,
        center_y: float,
        bbox_size: float = None,
        max_features: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        하천 데이터 조회 (캐싱 적용)
        
        Args:
            center_x, center_y: 중심 좌표 (EPSG:3857)
            bbox_size: BBox 크기 (미터)
            max_features: 최대 피처 수
        
        Returns:
            하천 피처 리스트
        """
        bbox = calculate_bbox(center_x, center_y, bbox_size or settings.BBOX_SIZE)
        layer = BASE_LAYERS["river"]
        
        cache_key = WFSCache.generate_key(self.base_wfs_url, bbox, "river")
        
        xml = build_getfeature_xml(
            layer_name=layer.name,
            geometry_field=layer.geometry_field,
            bbox=bbox,
            max_features=max_features
        )
        
        return await self._fetch_features(self.base_wfs_url, xml, cache_key)
    
    @profile_async
    async def get_all_data(
        self,
        center_x: float,
        center_y: float,
        bbox_size: float = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        모든 필요 데이터 일괄 조회 (병렬 요청)
        
        Args:
            center_x, center_y: 중심 좌표 (EPSG:3857)
            bbox_size: BBox 크기 (미터)
        
        Returns:
            레이어별 피처 딕셔너리
            - poles: 전주
            - lines: 전선 (고압)
            - transformers: 변압기/인입선 (저압선 포함)
            - roads: 도로
            - buildings: 건물
        """
        import asyncio
        
        # 병렬 요청 (연결 풀 공유)
        # 변압기 레이어도 함께 조회 (저압선 데이터 포함)
        poles_task = self.get_poles(center_x, center_y, bbox_size)
        lines_task = self.get_lines(center_x, center_y, bbox_size)
        transformers_task = self.get_transformers(center_x, center_y, bbox_size)
        roads_task = self.get_roads(center_x, center_y, bbox_size)
        buildings_task = self.get_buildings(center_x, center_y, bbox_size)
        
        poles, lines, transformers, roads, buildings = await asyncio.gather(
            poles_task, lines_task, transformers_task, roads_task, buildings_task
        )
        
        # 캐시 통계 로깅
        stats = self.get_cache_stats()
        logger.debug(f"WFS 캐시 통계: {stats}")
        
        return {
            "poles": poles,
            "lines": lines,
            "transformers": transformers,  # 저압선 데이터 포함
            "roads": roads,
            "buildings": buildings
        }
    
    @profile_async
    async def get_facilities_by_bbox(
        self,
        min_x: float,
        min_y: float,
        max_x: float,
        max_y: float,
        max_features: int = 5000
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        BBox 기반 모든 시설물 조회 (화면 영역 기준)
        
        Args:
            min_x, min_y, max_x, max_y: BBox 좌표 (EPSG:3857)
            max_features: 레이어별 최대 피처 수 (기본 5000)
        
        Returns:
            레이어별 피처 딕셔너리 (전주, 전선, 변압기, 도로, 건물, 철도, 하천)
        """
        import asyncio
        
        bbox = (min_x, min_y, max_x, max_y)
        
        # 각 레이어에 대한 요청 생성 함수
        async def fetch_layer(layer_key: str, layers_dict: Dict, wfs_url: str) -> List[Dict[str, Any]]:
            layer = layers_dict[layer_key]
            cache_key = WFSCache.generate_key(wfs_url, bbox, layer_key)
            
            xml = build_getfeature_xml(
                layer_name=layer.name,
                geometry_field=layer.geometry_field,
                bbox=bbox,
                max_features=max_features
            )
            
            return await self._fetch_features(wfs_url, xml, cache_key)
        
        # 병렬 요청 생성
        tasks = [
            fetch_layer("pole", GIS_LAYERS, self.gis_wfs_url),
            fetch_layer("line", GIS_LAYERS, self.gis_wfs_url),
            fetch_layer("transformer", GIS_LAYERS, self.gis_wfs_url),
            fetch_layer("road", BASE_LAYERS, self.base_wfs_url),
            fetch_layer("building", BASE_LAYERS, self.base_wfs_url),
            fetch_layer("railway", BASE_LAYERS, self.base_wfs_url),
            fetch_layer("river", BASE_LAYERS, self.base_wfs_url),
        ]
        
        results = await asyncio.gather(*tasks)
        
        # 캐시 통계 로깅
        stats = self.get_cache_stats()
        logger.info(f"WFS 캐시 통계: {stats}")
        
        return {
            "poles": results[0],
            "lines": results[1],
            "transformers": results[2],
            "roads": results[3],
            "buildings": results[4],
            "railways": results[5],
            "rivers": results[6]
        }