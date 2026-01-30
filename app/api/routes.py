"""
ELBIX AIDD API 라우터
- 배전 설계 API 엔드포인트 정의
- 시설물 조회 API 엔드포인트 정의
"""

from fastapi import APIRouter, HTTPException, Query, Request, Depends
from typing import List, Optional
from shapely.geometry import shape, Point, LineString, Polygon, MultiPolygon
import logging

from app.models.request import DesignRequest
from app.models.response import DesignResponse, RouteResult
from app.config import settings
from app.api.auth import require_auth
from app.core.preprocessor import DataPreprocessor
from app.core.wfs_client import WFSClient

# API 라우터 생성
router = APIRouter(tags=["design"])

logger = logging.getLogger(__name__)

def parse_geometry(geom_data):
    """GeoJSON 지오메트리를 좌표로 변환"""
    if not geom_data:
        return None
    try:
        geom = shape(geom_data)
        if isinstance(geom, Point):
            return [geom.x, geom.y]
        elif isinstance(geom, LineString):
            return [list(c) for c in geom.coords]
        elif isinstance(geom, (Polygon, MultiPolygon)):
            if isinstance(geom, MultiPolygon):
                geom = list(geom.geoms)[0] if geom.geoms else None
            if geom:
                return [list(c) for c in geom.exterior.coords]
        return None
    except Exception as e:
        logger.warning(f"지오메트리 파싱 오류: {e}")
        return None

@router.post("/design", response_model=DesignResponse)
async def create_design(
    request: DesignRequest,
    username: str = Depends(require_auth)
) -> DesignResponse:
    from app.core.design_engine import DesignEngine
    try:
        engine = DesignEngine(
            gis_wfs_url=request.gis_wfs_url or settings.GIS_WFS_URL,
            base_wfs_url=request.base_wfs_url or settings.BASE_WFS_URL,
            eps_url=request.eps_url or settings.EPS_BASE_URL
        )
        result = await engine.run(coord=request.coord, phase_code=request.phase_code)
        return result
    except Exception as e:
        logger.exception("설계 처리 중 치명적 오류 발생")
        raise HTTPException(status_code=500, detail=f"설계 처리 중 오류 발생: {str(e)}")

@router.get("/design/status")
async def get_design_status():
    return {
        "service": "design",
        "status": "available",
        "max_distance_limit": settings.MAX_DISTANCE_LIMIT,
        "supported_phases": [settings.PHASE_SINGLE, settings.PHASE_THREE]
    }

@router.get("/facilities")
async def get_facilities(
    bbox: str = Query(None, description="영역 (EPSG:3857, 'minX,minY,maxX,maxY' 형식)"),
    coord: str = Query(None, description="중심 좌표 (EPSG:3857, 'x,y' 형식)"),
    bbox_size: float = Query(400.0, description="조회 영역 크기 (미터)"),
    max_features: int = Query(5000, le=5000, description="레이어별 최대 피처 수 (최대 5000)"),
    gis_wfs_url: Optional[str] = Query(None, description="GIS WFS URL (선택)"),
    base_wfs_url: Optional[str] = Query(None, description="BASE WFS URL (선택)"),
):
    try:
        wfs_client = WFSClient(
            gis_wfs_url=gis_wfs_url or settings.GIS_WFS_URL,
            base_wfs_url=base_wfs_url or settings.BASE_WFS_URL
        )
        
        if bbox:
            parts = bbox.split(',')
            if len(parts) != 4:
                raise HTTPException(status_code=400, detail="bbox 형식이 올바르지 않습니다.")
            min_x, min_y, max_x, max_y = map(float, parts)
        elif coord:
            parts = coord.split(',')
            x, y = float(parts[0]), float(parts[1])
            half_size = bbox_size / 2
            min_x, min_y = x - half_size, y - half_size
            max_x, max_y = x + half_size, y + half_size
        else:
            raise HTTPException(status_code=400, detail="bbox 또는 coord 파라미터가 필요합니다.")
        
        # 1. 데이터 수집
        raw_data = await wfs_client.get_facilities_by_bbox(min_x, min_y, max_x, max_y, max_features)
        
        # 2. 전처리 및 계통 복원 로직 적용
        preprocessor = DataPreprocessor()
        processed_data = preprocessor.process(raw_data)
        
        # 3. 프론트엔드 포맷 변환
        poles = [{
            "id": p.id, "coord": p.coord, "coordinates": p.coord,
            "pole_type": p.pole_type, "phase_code": p.phase_code, "properties": p.properties
        } for p in processed_data.poles]
        
        lines = [{
            "id": l.id, "coordinates": l.coords, "line_type": l.line_type,
            "phase_code": l.phase_code, "is_obstacle": l.is_obstacle,
            "is_service_drop": l.is_service_drop, "properties": l.properties
        } for l in processed_data.lines]
        
        # HV/LV 분리
        lines_hv = [l for l in lines if l["line_type"] == "HV"]
        lines_lv = [l for l in lines if l["line_type"] == "LV"]
        
        transformers = [{
            "id": tr.id,
            "coordinates": tr.coord,
            "capacity_kva": tr.capacity_kva,
            "phase_code": tr.phase_code,
            "pole_id": tr.pole_id,
            "properties": tr.properties
        } for tr in processed_data.transformers]

        response = {
            "status": "success",
            "poles": poles, 
            "lines": lines, # 호환성 유지
            "lines_hv": lines_hv, # 신규 분리
            "lines_lv": lines_lv, # 신규 분리
            "transformers": transformers,
            "roads": [{"id": r.id, "coordinates": r.coords} for r in processed_data.roads],
            "buildings": [{"id": b.id, "coordinates": list(b.geometry.exterior.coords)} for b in processed_data.buildings],
            "count": {
                "poles": len(poles), 
                "lines": len(lines), 
                "lines_hv": len(lines_hv),
                "lines_lv": len(lines_lv),
                "transformers": len(transformers),
                "roads": len(processed_data.roads), 
                "buildings": len(processed_data.buildings)
            },
            "bbox": {"min": [min_x, min_y], "max": [max_x, max_y]}
        }
        return response
    except Exception as e:
        logger.exception("시설물 조회 중 예외 발생")
        raise HTTPException(status_code=500, detail=str(e))
