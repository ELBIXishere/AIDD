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
    "line_hv": WFSLayer(
        name=settings.LAYER_LINE_HV,
        geometry_field=settings.GEOM_LINE,
        wfs_url=settings.GIS_WFS_URL
    ),
    "line_lv": WFSLayer(
        name=settings.LAYER_LINE_LV,
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
    "lake": WFSLayer(
        name=settings.LAYER_LAKE,
        geometry_field=settings.GEOM_LAKE,
        wfs_url=settings.BASE_WFS_URL
    ),
}

# 레이어별 필수 필드 리스트 (가시성 및 분석용)
LAYER_PROPS = {
    "pole": ["GID", "POLE_ID", "POLE_FORM_CD", "POLE_KND_CD", "POLE_SPEC_CD", "FAC_STAT_CD", "LINE_NO", "LINE_NM"],
    "line_hv": ["GID", "PRWR_KND_CD", "PHAR_CLCD", "VOLT_VAL", "FAC_STAT_CD", "LWER_FAC_GID", "UPPO_FAC_GID", "TEXT_GIS_ANNXN"],
    "line_lv": ["GID", "PRWR_KND_CD", "PHAR_CLCD", "VOLT_VAL", "FAC_STAT_CD", "LWER_FAC_GID", "UPPO_FAC_GID", "TEXT_GIS_ANNXN"],
    "transformer": ["GID", "TEXT_GIS_ANNXN", "PHAR_CLCD", "FAC_STAT_CD", "CAP_KVA", "TR_TYPE", "LVW_KND_CD", "NEWI_KND_CD", "POLE_ID"],
    "road": ["ROAD_ID", "FTR_IDN", "ROAD_TYPE"],
    "building": ["BLDG_ID", "FTR_IDN", "BLDG_TYPE"]
}


def build_getfeature_xml(
    layer_name: str,
    geometry_field: str,
    bbox: Tuple[float, float, float, float],
    srs_name: str = "EPSG:3857",
    max_features: int = 1000,
    property_names: List[str] = None
) -> str:
    """
    WFS GetFeature 요청 XML 생성 (필드 필터링 지원)
    """
    min_x, min_y, max_x, max_y = bbox
    
    # 필드 선별 로직 추가 (데이터 전송량 최적화)
    props_xml = ""
    if property_names:
        # 지오메트리 필드 강제 포함
        final_props = set(property_names)
        final_props.add(geometry_field)
        props_xml = "".join([f'<wfs:PropertyName>{p}</wfs:PropertyName>' for p in final_props])
    
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
        {props_xml}
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


class WFSClient:
    """WFS 데이터 수집 클라이언트 (연결 풀링 + 캐싱 + 필드 최적화)"""
    
    def __init__(
        self,
        gis_wfs_url: str = None,
        base_wfs_url: str = None,
        timeout: float = None,
        use_cache: bool = True
    ):
        """
        WFS 클라이언트 초기화
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
        """
        # 캐시 확인
        if cache_key and self.use_cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached
        
        headers = {
            "Content-Type": "text/xml",
            "Accept": "application/json",
            # "Accept-Encoding": "gzip, deflate", # 압축 해제 오류로 인해 비활성화
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
        """전주 데이터 조회"""
        bbox = calculate_bbox(center_x, center_y, bbox_size or settings.BBOX_SIZE)
        layer = GIS_LAYERS["pole"]
        cache_key = WFSCache.generate_key(self.gis_wfs_url, bbox, "pole")
        
        xml = build_getfeature_xml(
            layer_name=layer.name,
            geometry_field=layer.geometry_field,
            bbox=bbox,
            property_names=LAYER_PROPS["pole"]
        )
        return await self._fetch_features(self.gis_wfs_url, xml, cache_key)
    
    @profile_async
    async def get_lines_hv(
        self,
        center_x: float,
        center_y: float,
        bbox_size: float = None
    ) -> List[Dict[str, Any]]:
        """고압전선 데이터 조회"""
        bbox = calculate_bbox(center_x, center_y, bbox_size or settings.BBOX_SIZE)
        layer = GIS_LAYERS["line_hv"]
        cache_key = WFSCache.generate_key(self.gis_wfs_url, bbox, "line_hv")
        
        xml = build_getfeature_xml(
            layer_name=layer.name,
            geometry_field=layer.geometry_field,
            bbox=bbox,
            property_names=LAYER_PROPS["line_hv"]
        )
        return await self._fetch_features(self.gis_wfs_url, xml, cache_key)

    @profile_async
    async def get_lines_lv(
        self,
        center_x: float,
        center_y: float,
        bbox_size: float = None
    ) -> List[Dict[str, Any]]:
        """저압전선 데이터 조회"""
        bbox = calculate_bbox(center_x, center_y, bbox_size or settings.BBOX_SIZE)
        layer = GIS_LAYERS["line_lv"]
        cache_key = WFSCache.generate_key(self.gis_wfs_url, bbox, "line_lv")
        
        xml = build_getfeature_xml(
            layer_name=layer.name,
            geometry_field=layer.geometry_field,
            bbox=bbox,
            property_names=LAYER_PROPS["line_lv"]
        )
        return await self._fetch_features(self.gis_wfs_url, xml, cache_key)
    
    @profile_async
    async def get_roads(
        self,
        center_x: float,
        center_y: float,
        bbox_size: float = None
    ) -> List[Dict[str, Any]]:
        """도로 데이터 조회"""
        bbox = calculate_bbox(center_x, center_y, bbox_size or settings.BBOX_SIZE)
        layer = BASE_LAYERS["road"]
        cache_key = WFSCache.generate_key(self.base_wfs_url, bbox, "road")
        
        xml = build_getfeature_xml(
            layer_name=layer.name,
            geometry_field=layer.geometry_field,
            bbox=bbox,
            property_names=LAYER_PROPS["road"]
        )
        return await self._fetch_features(self.base_wfs_url, xml, cache_key)
    
    @profile_async
    async def get_buildings(
        self,
        center_x: float,
        center_y: float,
        bbox_size: float = None
    ) -> List[Dict[str, Any]]:
        """건물 데이터 조회"""
        bbox = calculate_bbox(center_x, center_y, bbox_size or settings.BBOX_SIZE)
        layer = BASE_LAYERS["building"]
        cache_key = WFSCache.generate_key(self.base_wfs_url, bbox, "building")
        
        xml = build_getfeature_xml(
            layer_name=layer.name,
            geometry_field=layer.geometry_field,
            bbox=bbox,
            property_names=LAYER_PROPS["building"]
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
        """변압기 데이터 조회"""
        bbox = calculate_bbox(center_x, center_y, bbox_size or settings.BBOX_SIZE)
        layer = GIS_LAYERS["transformer"]
        cache_key = WFSCache.generate_key(self.gis_wfs_url, bbox, "transformer")
        
        xml = build_getfeature_xml(
            layer_name=layer.name,
            geometry_field=layer.geometry_field,
            bbox=bbox,
            max_features=max_features,
            property_names=LAYER_PROPS["transformer"]
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
        """철도 데이터 조회"""
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
        """하천 데이터 조회"""
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
        """모든 필요 데이터 일괄 조회 (HV/LV 분리)"""
        import asyncio
        poles_task = self.get_poles(center_x, center_y, bbox_size)
        lines_hv_task = self.get_lines_hv(center_x, center_y, bbox_size)
        lines_lv_task = self.get_lines_lv(center_x, center_y, bbox_size)
        transformers_task = self.get_transformers(center_x, center_y, bbox_size)
        roads_task = self.get_roads(center_x, center_y, bbox_size)
        buildings_task = self.get_buildings(center_x, center_y, bbox_size)
        
        poles, lines_hv, lines_lv, transformers, roads, buildings = await asyncio.gather(
            poles_task, lines_hv_task, lines_lv_task, transformers_task, roads_task, buildings_task
        )
        return {
            "poles": poles, 
            "lines_hv": lines_hv, 
            "lines_lv": lines_lv,
            "lines": lines_hv + lines_lv,  # 호환성용
            "transformers": transformers, 
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
        """BBox 기반 모든 시설물 조회 (HV/LV 분리)"""
        import asyncio
        bbox = (min_x, min_y, max_x, max_y)
        
        async def fetch_layer(layer_key: str, layers_dict: Dict, wfs_url: str) -> List[Dict[str, Any]]:
            layer = layers_dict[layer_key]
            cache_key = WFSCache.generate_key(wfs_url, bbox, layer_key)
            # 필드 필터링 적용
            props = LAYER_PROPS.get(layer_key)
            xml = build_getfeature_xml(
                layer_name=layer.name,
                geometry_field=layer.geometry_field,
                bbox=bbox,
                max_features=max_features,
                property_names=props
            )
            return await self._fetch_features(wfs_url, xml, cache_key)
        
        tasks = [
            fetch_layer("pole", GIS_LAYERS, self.gis_wfs_url),
            fetch_layer("line_hv", GIS_LAYERS, self.gis_wfs_url),
            fetch_layer("line_lv", GIS_LAYERS, self.gis_wfs_url),
            fetch_layer("transformer", GIS_LAYERS, self.gis_wfs_url),
            fetch_layer("road", BASE_LAYERS, self.base_wfs_url),
            fetch_layer("building", BASE_LAYERS, self.base_wfs_url),
            fetch_layer("railway", BASE_LAYERS, self.base_wfs_url),
            fetch_layer("river", BASE_LAYERS, self.base_wfs_url),
        ]
        results = await asyncio.gather(*tasks)
        return {
            "poles": results[0], 
            "lines_hv": results[1], 
            "lines_lv": results[2],
            "lines": results[1] + results[2], # 호환성용
            "transformers": results[3],
            "roads": results[4], 
            "buildings": results[5], 
            "railways": results[6], 
            "rivers": results[7]
        }
