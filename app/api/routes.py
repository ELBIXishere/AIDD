"""
ELBIX AIDD API 라우터
- 배전 설계 API 엔드포인트 정의
- 시설물 조회 API 엔드포인트 정의
"""

from fastapi import APIRouter, HTTPException, Query, Request, Depends
from typing import List, Optional

from app.models.request import DesignRequest
from app.models.response import DesignResponse, RouteResult
from app.config import settings
from app.api.auth import require_auth

# API 라우터 생성
router = APIRouter(tags=["design"])


@router.post("/design", response_model=DesignResponse)
async def create_design(
    request: DesignRequest,
    username: str = Depends(require_auth)
) -> DesignResponse:
    """
    배전 설계 API
    
    수용가 좌표와 신청 규격을 입력받아 최적의 배전 경로를 계산합니다.
    
    - **coord**: 수용가 좌표 (EPSG:3857, "x,y" 형식)
    - **phase_code**: 신청 규격 ("1": 단상, "3": 3상)
    
    Returns:
        공사비 순으로 정렬된 배전 설계 경로 목록
    """
    # TODO: 실제 설계 로직 연동
    # 1. WFS 데이터 수집
    # 2. 데이터 전처리
    # 3. 후보 전주 선별
    # 4. 도로 네트워크 그래프 구축
    # 5. 경로 탐색
    # 6. 신설 전주 배치
    # 7. 공사비 계산
    # 8. 결과 반환
    
    from app.core.design_engine import DesignEngine
    
    try:
        engine = DesignEngine(
            gis_wfs_url=request.gis_wfs_url or settings.GIS_WFS_URL,
            base_wfs_url=request.base_wfs_url or settings.BASE_WFS_URL,
            eps_url=request.eps_url or settings.EPS_BASE_URL
        )
        
        result = await engine.run(
            coord=request.coord,
            phase_code=request.phase_code
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"설계 처리 중 오류 발생: {str(e)}"
        )


@router.get("/design/status")
async def get_design_status():
    """설계 서비스 상태 확인"""
    return {
        "service": "design",
        "status": "available",
        "max_distance_limit": settings.MAX_DISTANCE_LIMIT,
        "supported_phases": [settings.PHASE_SINGLE, settings.PHASE_THREE]
    }


@router.get("/facilities")
async def get_facilities(
    bbox: str = Query(None, description="영역 (EPSG:3857, 'minX,minY,maxX,maxY' 형식)"),
    coord: str = Query(None, description="[deprecated] 중심 좌표 (EPSG:3857, 'x,y' 형식)"),
    bbox_size: float = Query(400.0, description="[deprecated] 조회 영역 크기 (미터)"),
    max_features: int = Query(5000, le=5000, description="레이어별 최대 피처 수 (최대 5000)"),
    gis_wfs_url: Optional[str] = Query(None, description="GIS WFS URL (선택)"),
    base_wfs_url: Optional[str] = Query(None, description="BASE WFS URL (선택)"),
):
    """
    시설물 조회 API (인증 없이 호출 가능)
    
    지정된 영역(bbox) 내의 모든 시설물을 조회합니다.
    도메인/프록시 환경에서 세션 쿠키가 불안정할 때 시설물 표시가 동작하도록 인증을 optional로 둠.
    설계 실행 등 다른 API는 기존대로 require_auth 유지.
    
    - **bbox**: 영역 (EPSG:3857, "minX,minY,maxX,maxY" 형식) [권장]
    - **coord**: [deprecated] 중심 좌표 (호환성을 위해 유지)
    - **max_features**: 레이어별 최대 피처 수 (기본 5000, 최대 5000)
    
    Returns:
        전주, 전선, 변압기, 도로, 건물, 철도, 하천 목록 및 좌표 정보
    """
    from app.core.wfs_client import WFSClient
    from shapely.geometry import shape, Point, LineString, Polygon, MultiPolygon
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # WFS 클라이언트 생성
        wfs_client = WFSClient(
            gis_wfs_url=gis_wfs_url or settings.GIS_WFS_URL,
            base_wfs_url=base_wfs_url or settings.BASE_WFS_URL
        )
        
        # BBox 파싱
        if bbox:
            # 새로운 bbox 파라미터 사용
            parts = bbox.split(',')
            if len(parts) != 4:
                raise HTTPException(
                    status_code=400, 
                    detail="bbox 형식이 올바르지 않습니다. 'minX,minY,maxX,maxY' 형식으로 입력하세요."
                )
            min_x, min_y, max_x, max_y = map(float, parts)
        elif coord:
            # deprecated: 기존 coord 파라미터로 bbox 계산
            parts = coord.split(',')
            if len(parts) != 2:
                raise HTTPException(
                    status_code=400, 
                    detail="좌표 형식이 올바르지 않습니다. 'x,y' 형식으로 입력하세요."
                )
            x, y = float(parts[0]), float(parts[1])
            half_size = bbox_size / 2
            min_x, min_y = x - half_size, y - half_size
            max_x, max_y = x + half_size, y + half_size
        else:
            raise HTTPException(
                status_code=400,
                detail="bbox 또는 coord 파라미터가 필요합니다."
            )
        
        logger.info(f"시설물 조회 BBox: [{min_x}, {min_y}, {max_x}, {max_y}], max_features={max_features}")
        
        # 데이터 수집 (bbox 기반, 레이어별 max_features 제한)
        raw_data = await wfs_client.get_facilities_by_bbox(
            min_x=min_x,
            min_y=min_y,
            max_x=max_x,
            max_y=max_y,
            max_features=max_features
        )
        
        # 응답 형식으로 변환
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
                        # MultiPolygon의 경우 첫 번째 폴리곤 사용
                        geom = list(geom.geoms)[0] if geom.geoms else None
                    if geom:
                        return [list(c) for c in geom.exterior.coords]
                return None
            except Exception as e:
                logger.warning(f"지오메트리 파싱 오류: {e}")
                return None
        
        # 전주 데이터 변환
        poles = []
        for feature in raw_data.get("poles", []):
            props = feature.get("properties", {})
            geom = feature.get("geometry")
            coords = parse_geometry(geom)
            if coords:
                # 상 코드 판단 - 연결된 전선 정보에서 추출 가능
                phar_clcd = props.get("PHAR_CLCD", "")
                if phar_clcd in ["CBA", "ABC", "RST", "3", "3P"] or (phar_clcd and len(phar_clcd) >= 3):
                    phase_code = "3"
                else:
                    phase_code = "1"
                
                poles.append({
                    "id": str(props.get("GID", props.get("POLE_ID", ""))),
                    "coordinates": coords,
                    "phase_code": phase_code,
                    "pole_type": props.get("POLE_FORM_CD", "H"),  # 기본값 고압
                    "is_high_voltage": props.get("POLE_FORM_CD") != "L"
                })
        
        # 전선 데이터 변환
        lines = []
        for feature in raw_data.get("lines", []):
            props = feature.get("properties", {})
            geom = feature.get("geometry")
            coords = parse_geometry(geom)
            if coords and len(coords) >= 2:
                # 상 코드 판단
                phar_clcd = props.get("PHAR_CLCD", "")
                if phar_clcd in ["CBA", "ABC", "RST", "3", "3P"] or (phar_clcd and len(phar_clcd) >= 3):
                    phase_code = "3"
                else:
                    phase_code = "1"
                
                # 전압 레벨 판단
                prwr_knd = props.get("PRWR_KND_CD", "")
                line_type = "LV" if prwr_knd in ["LV", "L"] else "HV"
                
                lines.append({
                    "id": str(props.get("GID", props.get("LINE_ID", ""))),
                    "coordinates": coords,
                    "line_type": line_type,
                    "phase_code": phase_code
                })
        
        # 변압기 데이터 변환
        transformers = []
        for feature in raw_data.get("transformers", []):
            props = feature.get("properties", {})
            geom = feature.get("geometry")
            coords = parse_geometry(geom)
            if coords:
                transformers.append({
                    "id": str(props.get("GID", props.get("TR_ID", ""))),
                    "coordinates": coords if isinstance(coords[0], list) else [coords],
                    "capacity_kva": props.get("CAP_KVA", 0),
                    "transformer_type": props.get("TR_TYPE", "")
                })
        
        # 도로 데이터 변환
        roads = []
        for feature in raw_data.get("roads", []):
            props = feature.get("properties", {})
            geom = feature.get("geometry")
            coords = parse_geometry(geom)
            if coords and len(coords) >= 2:
                roads.append({
                    "id": str(props.get("ROAD_ID", props.get("FTR_IDN", ""))),
                    "coordinates": coords,
                    "road_type": props.get("ROAD_TYPE", "")
                })
        
        # 건물 데이터 변환
        buildings = []
        for feature in raw_data.get("buildings", []):
            props = feature.get("properties", {})
            geom = feature.get("geometry")
            coords = parse_geometry(geom)
            if coords:
                buildings.append({
                    "id": str(props.get("BLDG_ID", props.get("FTR_IDN", ""))),
                    "coordinates": coords,
                    "building_type": props.get("BLDG_TYPE", "")
                })
        
        # 철도 데이터 변환
        railways = []
        for feature in raw_data.get("railways", []):
            props = feature.get("properties", {})
            geom = feature.get("geometry")
            coords = parse_geometry(geom)
            if coords:
                railways.append({
                    "id": str(props.get("RAIL_ID", props.get("FTR_IDN", ""))),
                    "coordinates": coords,
                    "railway_type": props.get("RAIL_TYPE", "")
                })
        
        # 하천 데이터 변환
        rivers = []
        for feature in raw_data.get("rivers", []):
            props = feature.get("properties", {})
            geom = feature.get("geometry")
            coords = parse_geometry(geom)
            if coords:
                rivers.append({
                    "id": str(props.get("RIVER_ID", props.get("FTR_IDN", ""))),
                    "coordinates": coords,
                    "river_type": props.get("RIVER_TYPE", "")
                })
        
        response = {
            "poles": poles,
            "lines": lines,
            "transformers": transformers,
            "roads": roads,
            "buildings": buildings,
            "railways": railways,
            "rivers": rivers,
            "count": {
                "poles": len(poles),
                "lines": len(lines),
                "transformers": len(transformers),
                "roads": len(roads),
                "buildings": len(buildings),
                "railways": len(railways),
                "rivers": len(rivers)
            },
            "bbox": {
                "min": [min_x, min_y],
                "max": [max_x, max_y]
            }
        }
        
        logger.info(f"시설물 조회 결과: {response['count']}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"시설물 조회 오류: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"시설물 조회 중 오류 발생: {str(e)}"
        )
