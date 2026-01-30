"""
ELBIX AIDD 설계 엔진 v2
- 전체 처리 흐름 통합
- WFS 수집 → 전처리 → 후보 선별 → 그래프 구축 → 경로 탐색 → 전주 배치 → 비용 계산
- 전압 강하 계산 및 변압기 용량 검증 추가
- 병렬 처리 및 성능 최적화 적용
"""

import time
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import logging
from concurrent.futures import ThreadPoolExecutor

from app.config import settings
from app.utils.profiler import profile_async, profile_block, get_profiling_summary
from app.core.wfs_client import WFSClient
from app.core.preprocessor import DataPreprocessor, ProcessedData
from app.core.target_selector import TargetSelector, SelectionResult
from app.core.graph_builder import RoadGraphBuilder, RoadGraph
from app.core.pathfinder import Pathfinder, PathfindingResult
from app.core.pole_allocator import PoleAllocator, AllocationResult
from app.core.cost_calculator import CostCalculator, CostResult, PoleSpec, WireSpec
from app.core.line_validator import LineValidator, ValidationResult
from app.core.eps_client import EPSClient
from app.core.voltage_calculator import VoltageCalculator, WireType
from app.core.capacity_validator import CapacityValidator, TransformerInfo
from app.models.response import (
    DesignResponse, DesignStatus, RouteResult,
    VoltageDropInfo, CapacityInfo, DetailedCostBreakdown,
    MaterialCostDetail, LaborCostDetail, CostDetailItem
)

logger = logging.getLogger(__name__)


class DesignEngine:
    """배전 설계 엔진 v2"""
    
    def __init__(
        self,
        gis_wfs_url: str = None,
        base_wfs_url: str = None,
        eps_url: str = None
    ):
        """
        Args:
            gis_wfs_url: GIS WFS 서버 URL
            base_wfs_url: BASE WFS 서버 URL
            eps_url: EPS 서버 URL
        """
        self.gis_wfs_url = gis_wfs_url or settings.GIS_WFS_URL
        self.base_wfs_url = base_wfs_url or settings.BASE_WFS_URL
        self.eps_url = eps_url or settings.EPS_BASE_URL
        
        # 클라이언트 초기화
        self.wfs_client = WFSClient(
            gis_wfs_url=self.gis_wfs_url,
            base_wfs_url=self.base_wfs_url
        )
        
        # EPS 클라이언트 초기화
        self.eps_client = EPSClient(eps_url=self.eps_url)
        
        # 전압 강하 계산기
        self.voltage_calculator = VoltageCalculator()
        
        # 변압기 용량 검증기
        self.capacity_validator = CapacityValidator()
    
    @profile_async
    async def run(
        self,
        coord: str,
        phase_code: str,
        requested_load_kw: float = 5.0
    ) -> DesignResponse:
        """
        배전 설계 실행 (병렬 처리 적용)
        
        Args:
            coord: 수용가 좌표 (EPSG:3857, "x,y" 형식)
            phase_code: 신청 상 코드 ("1": 단상, "3": 3상)
            requested_load_kw: 신청 부하 (kW, 기본 5kW)
        
        Returns:
            설계 응답
        """
        start_time = time.time()
        
        # 좌표 파싱
        try:
            parts = coord.split(',')
            consumer_x = float(parts[0].strip())
            consumer_y = float(parts[1].strip())
            consumer_coord = (consumer_x, consumer_y)
        except Exception as e:
            return DesignResponse(
                status=DesignStatus.FAILED,
                request_spec=self._get_phase_name(phase_code),
                consumer_coord=[0, 0],
                error_message=f"좌표 파싱 오류: {str(e)}"
            )
        
        logger.info(f"설계 시작: 좌표={consumer_coord}, 상={phase_code}, 부하={requested_load_kw}kW")
        
        try:
            # Phase 1: WFS 데이터 수집
            logger.info("Phase 1: WFS 데이터 수집 중...")
            raw_data = await self.wfs_client.get_all_data(
                consumer_x, consumer_y,
                settings.BBOX_SIZE
            )
            
            logger.info(
                f"데이터 수집 완료: 전주 {len(raw_data['poles'])}개, "
                f"전선 {len(raw_data['lines'])}개, "
                f"도로 {len(raw_data['roads'])}개, "
                f"건물 {len(raw_data['buildings'])}개"
            )
            
            # Phase 2: 데이터 전처리
            logger.info("Phase 2: 데이터 전처리 중...")
            preprocessor = DataPreprocessor()
            processed_data = preprocessor.process(raw_data)
            
            if not processed_data.poles:
                return DesignResponse(
                    status=DesignStatus.NO_ROUTE,
                    request_spec=self._get_phase_name(phase_code),
                    consumer_coord=[consumer_x, consumer_y],
                    error_message="영역 내에 유효한 전주가 없습니다.",
                    requested_load_kw=requested_load_kw
                )
            
            # Phase 3: 후보 전주 선별
            logger.info("Phase 3: 후보 전주 선별 중...")
            selector = TargetSelector(processed_data)
            selection_result = selector.select(consumer_coord, phase_code)
            
            if not selection_result.targets:
                return DesignResponse(
                    status=DesignStatus.NO_ROUTE,
                    request_spec=self._get_phase_name(phase_code),
                    consumer_coord=[consumer_x, consumer_y],
                    error_message=selection_result.message,
                    requested_load_kw=requested_load_kw
                )
            
            logger.info(f"후보 전주: {len(selection_result.targets)}개")
            
            # Fast Track 체크
            if selection_result.fast_track_targets:
                logger.info(f"Fast Track 후보: {len(selection_result.fast_track_targets)}개 발견")
            
            # Phase 4: 도로 없으면 Fast Track만 처리
            if not processed_data.roads:
                if selection_result.fast_track_targets:
                    return self._create_fast_track_response(
                        consumer_coord, phase_code,
                        selection_result.fast_track_targets,
                        start_time, requested_load_kw,
                        processed_data
                    )
                else:
                    return DesignResponse(
                        status=DesignStatus.NO_ROUTE,
                        request_spec=self._get_phase_name(phase_code),
                        consumer_coord=[consumer_x, consumer_y],
                        error_message="영역 내에 도로가 없어 경로를 생성할 수 없습니다.",
                        requested_load_kw=requested_load_kw
                    )
            
            # Phase 4: 도로 네트워크 그래프 구축
            logger.info("Phase 4: 도로 네트워크 그래프 구축 중...")
            graph_builder = RoadGraphBuilder(processed_data)
            road_graph = graph_builder.build(consumer_coord, selection_result.targets)
            
            if not road_graph.pole_node_ids:
                if selection_result.fast_track_target:
                    return self._create_fast_track_response(
                        consumer_coord, phase_code,
                        selection_result.fast_track_target,
                        start_time, requested_load_kw
                    )
                else:
                    return DesignResponse(
                        status=DesignStatus.NO_ROUTE,
                        request_spec=self._get_phase_name(phase_code),
                        consumer_coord=[consumer_x, consumer_y],
                        error_message="전주를 도로와 연결할 수 없습니다.",
                        requested_load_kw=requested_load_kw
                    )
            
            # Phase 5: 경로 탐색
            logger.info("Phase 5: 경로 탐색 중...")
            pathfinder = Pathfinder(road_graph)
            pathfinding_result = pathfinder.find_paths(selection_result.targets, max_paths=10)
            
            if not pathfinding_result.paths:
                return DesignResponse(
                    status=DesignStatus.NO_ROUTE,
                    request_spec=self._get_phase_name(phase_code),
                    consumer_coord=[consumer_x, consumer_y],
                    error_message="유효한 경로가 없습니다 (400m 초과 또는 도달 불가)",
                    requested_load_kw=requested_load_kw
                )
            
            logger.info(f"유효 경로: {len(pathfinding_result.paths)}개")
            
            # Phase 5.5: 전선 교차 검증 (FR-05)
            logger.info("Phase 5.5: 전선 교차 검증 중...")
            line_validator = LineValidator(processed_data)
            valid_paths = []
            
            # 신설 선로 타입 결정 (높이 추정용)
            new_line_type = "HV" if phase_code == settings.PHASE_THREE else "LV"
            
            for path in pathfinding_result.paths:
                validation = line_validator.validate_path(path.path_coords, new_line_type=new_line_type)
                if validation.is_valid:
                    valid_paths.append(path)
                else:
                    logger.info(f"경로 제외 (전선 교차): {path.target_pole_id} - {validation.message}")
            
            pathfinding_result.paths = valid_paths
            
            if not pathfinding_result.paths:
                return DesignResponse(
                    status=DesignStatus.NO_ROUTE,
                    request_spec=self._get_phase_name(phase_code),
                    consumer_coord=[consumer_x, consumer_y],
                    error_message="모든 경로가 기존 전선과 교차하여 유효한 경로가 없습니다",
                    requested_load_kw=requested_load_kw
                )
            
            logger.info(f"전선 교차 검증 후 유효 경로: {len(pathfinding_result.paths)}개")
            
            # Phase 6: 신설 전주 배치 (병렬 처리)
            logger.info("Phase 6: 신설 전주 배치 중...")
            with profile_block("전주 배치"):
                allocator = PoleAllocator()
                allocation_results = await self._allocate_poles_parallel(allocator, pathfinding_result.paths)
            
            # Phase 7: 공사비 계산 (병렬 처리)
            logger.info("Phase 7: 공사비 계산 중...")
            with profile_block("공사비 계산"):
                calculator = CostCalculator(detailed_mode=True)
                cost_results = calculator.calculate_batch(allocation_results)
            
            # Phase 8: EPS 서버 검증
            logger.info("Phase 8: EPS 서버 검증 중...")
            try:
                eps_available = await self.eps_client.health_check()
                if eps_available:
                    top_pole_ids = [r.start_pole_id for r in cost_results[:5]]
                    duplicate_check = await self.eps_client.check_network_duplicate(top_pole_ids)
                    
                    if duplicate_check.has_duplicate:
                        logger.warning(f"계통 중복 발견: {duplicate_check.message}")
                        for result in cost_results:
                            if result.start_pole_id in duplicate_check.duplicate_poles:
                                result.remark = (result.remark or "") + " | 계통 중복 주의"
                else:
                    logger.info("EPS 서버 연결 불가 - 검증 생략")
            except Exception as eps_error:
                logger.warning(f"EPS 검증 중 오류 (무시): {eps_error}")
            
            # Phase 9: 전압 강하 계산 및 결과 변환
            logger.info("Phase 9: 전압 강하 계산 및 결과 변환 중...")
            routes = self._convert_to_routes_v2(cost_results, phase_code, requested_load_kw, processed_data)
            
            elapsed_time = int((time.time() - start_time) * 1000)
            
            logger.info(f"설계 완료: {len(routes)}개 경로, {elapsed_time}ms 소요")
            
            return DesignResponse(
                status=DesignStatus.SUCCESS,
                request_spec=self._get_phase_name(phase_code),
                consumer_coord=[consumer_x, consumer_y],
                routes=routes,
                processing_time_ms=elapsed_time,
                requested_load_kw=requested_load_kw
            )
            
        except Exception as e:
            logger.exception(f"설계 처리 오류: {e}")
            elapsed_time = int((time.time() - start_time) * 1000)
            
            return DesignResponse(
                status=DesignStatus.FAILED,
                request_spec=self._get_phase_name(phase_code),
                consumer_coord=[consumer_x, consumer_y],
                error_message=str(e),
                processing_time_ms=elapsed_time,
                requested_load_kw=requested_load_kw
            )
    
    def _get_phase_name(self, phase_code: str) -> str:
        """상 코드를 한글 이름으로 변환"""
        return "3상" if phase_code == settings.PHASE_THREE else "단상"
    
    async def _allocate_poles_parallel(self, allocator: PoleAllocator, paths: List) -> List[AllocationResult]:
        """경로별 전주 배치 병렬 처리"""
        if len(paths) <= 2:
            return allocator.allocate_batch(paths)
        
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [loop.run_in_executor(executor, allocator.allocate, path) for path in paths]
            results = await asyncio.gather(*futures)
        return list(results)
    
    def _create_fast_track_response(
        self,
        consumer_coord: Tuple[float, float],
        phase_code: str,
        fast_track_targets: List,
        start_time: float,
        requested_load_kw: float,
        processed_data: ProcessedData = None
    ) -> DesignResponse:
        """다중 Fast Track 응답 생성 (도로가 없는 경우)"""
        routes = []
        for i, target in enumerate(fast_track_targets):
            distance = target.distance_to_consumer
            wire_cost = int(distance * settings.COST_WIRE_LV)
            labor_cost = settings.COST_LABOR_BASE
            total_cost = wire_cost + labor_cost
            
            # 전압값 확인
            voltage_override = None
            if hasattr(target, 'voltage') and target.voltage:
                 voltage_override = target.voltage
            elif hasattr(target, 'pole') and target.pole.voltage:
                 voltage_override = target.pole.voltage

            # 전압 강하 계산
            vd_result = self.voltage_calculator.calculate(
                distance=distance,
                load_kw=requested_load_kw,
                phase_type=phase_code,
                wire_type=WireType.OW_22,
                voltage_override=voltage_override
            )
            
            voltage_drop = VoltageDropInfo(
                distance_m=distance,
                load_kw=requested_load_kw,
                voltage_drop_v=vd_result.voltage_drop_v,
                voltage_drop_percent=vd_result.voltage_drop_percent,
                is_acceptable=vd_result.is_acceptable,
                limit_percent=vd_result.limit_percent,
                wire_spec="OW_22",
                message=vd_result.message
            )
            
            route = RouteResult(
                rank=i + 1,
                total_cost=total_cost,
                cost_index=int(distance), # Fast Track은 거리가 곧 인덱스
                total_distance=distance,
                start_pole_id=target.id,
                start_pole_coord=[target.coord[0], target.coord[1]],
                new_poles_count=0,
                path_coordinates=[
                    [consumer_coord[0], consumer_coord[1]],
                    [target.coord[0], target.coord[1]]
                ],
                new_pole_coordinates=[],
                wire_cost=wire_cost,
                pole_cost=0,
                labor_cost=labor_cost,
                remark="FastTrack - 40m 이내 직접 연결",
                voltage_drop=voltage_drop,
                wire_spec="OW_22"
            )
            routes.append(route)
        
        elapsed_time = int((time.time() - start_time) * 1000)
        
        return DesignResponse(
            status=DesignStatus.SUCCESS,
            request_spec=self._get_phase_name(phase_code),
            consumer_coord=[consumer_coord[0], consumer_coord[1]],
            routes=routes,
            processing_time_ms=elapsed_time,
            requested_load_kw=requested_load_kw
        )
    
    def _convert_to_routes_v2(
        self,
        cost_results: List[CostResult],
        phase_code: str,
        requested_load_kw: float,
        processed_data: ProcessedData = None
    ) -> List[RouteResult]:
        """CostResult를 RouteResult로 변환 (v2: 상세 정보 포함)"""
        routes = []
        
        # 기설 전주 정보 조회를 위한 맵 생성
        pole_map = {}
        pole_line_map = {}  # 전주 ID → 연결된 전선 리스트
        if processed_data:
            pole_map = {p.id: p for p in processed_data.poles}
            for line in processed_data.lines:
                if line.start_pole_id:
                    if line.start_pole_id not in pole_line_map:
                        pole_line_map[line.start_pole_id] = []
                    pole_line_map[line.start_pole_id].append(line)
                if line.end_pole_id:
                    if line.end_pole_id not in pole_line_map:
                        pole_line_map[line.end_pole_id] = []
                    pole_line_map[line.end_pole_id].append(line)
        
        for cost_result in cost_results:
            # 기설 전주 전압값 조회
            voltage_override = None
            if cost_result.start_pole_id and cost_result.start_pole_id in pole_map:
                start_pole = pole_map[cost_result.start_pole_id]
                if start_pole.voltage:
                    voltage_override = start_pole.voltage

            # 전압 강하 계산
            vd_result = self.voltage_calculator.calculate(
                distance=cost_result.total_distance,
                load_kw=requested_load_kw,
                phase_type=phase_code,
                wire_type=WireType.OW_22,
                voltage_override=voltage_override  # [NEW] 실제 전압값 적용
            )
            
            voltage_drop = VoltageDropInfo(
                distance_m=cost_result.total_distance,
                load_kw=requested_load_kw,
                voltage_drop_v=vd_result.voltage_drop_v,
                voltage_drop_percent=vd_result.voltage_drop_percent,
                is_acceptable=vd_result.is_acceptable,
                limit_percent=vd_result.limit_percent,
                wire_spec="OW_22",
                message=vd_result.message
            )
            
            # 상세 비용 변환
            detailed_cost = None
            if cost_result.detailed_breakdown:
                db = cost_result.detailed_breakdown
                detailed_cost = DetailedCostBreakdown(
                    material=MaterialCostDetail(
                        pole=CostDetailItem(
                            count=db.material.pole_count,
                            spec=db.material.pole_spec,
                            unit_cost=db.material.pole_unit_cost,
                            cost=db.material.pole_cost
                        ),
                        wire=CostDetailItem(
                            length=db.material.wire_length,
                            spec=db.material.wire_spec,
                            unit_cost=db.material.wire_unit_cost,
                            cost=db.material.wire_cost
                        ),
                        insulator=CostDetailItem(
                            count=db.material.insulator_count,
                            cost=db.material.insulator_cost
                        ),
                        arm_tie=CostDetailItem(
                            count=db.material.arm_tie_count,
                            cost=db.material.arm_tie_cost
                        ),
                        clamp=CostDetailItem(
                            count=db.material.clamp_count,
                            cost=db.material.clamp_cost
                        ),
                        connector=CostDetailItem(
                            count=db.material.connector_count,
                            cost=db.material.connector_cost
                        ),
                        total=db.material.total
                    ),
                    labor=LaborCostDetail(
                        pole_install=CostDetailItem(
                            count=db.labor.pole_install_count,
                            unit_cost=db.labor.pole_install_unit_cost,
                            cost=db.labor.pole_install_cost
                        ),
                        wire_stretch=CostDetailItem(
                            length=db.labor.wire_stretch_length,
                            unit_cost=db.labor.wire_stretch_unit_cost,
                            cost=db.labor.wire_stretch_cost
                        ),
                        insulator_install=CostDetailItem(
                            count=db.labor.insulator_install_count,
                            unit_cost=db.labor.insulator_install_unit_cost,
                            cost=db.labor.insulator_install_cost
                        ),
                        base=db.labor.base_labor_cost,
                        total=db.labor.total
                    ),
                    overhead_rate=db.overhead_rate,
                    overhead_cost=db.overhead_cost,
                    profit_rate=db.profit_rate,
                    profit_cost=db.profit_cost,
                    extra_cost=db.extra_cost,
                    extra_detail=db.extra_detail,
                    subtotal=db.subtotal,
                    total=db.total_cost
                )
            
            # 기설 전주의 전압/상 정보 조회 (복원된 계통 정보 활용)
            source_voltage_type = "LV" # 기본값
            source_phase_type = "1"
            
            if cost_result.start_pole_id and cost_result.start_pole_id in pole_map:
                pole_obj = pole_map[cost_result.start_pole_id]
                source_voltage_type = "HV" if pole_obj.pole_type == "H" else "LV"
                source_phase_type = pole_obj.phase_code or "1"
            
            route = RouteResult(
                rank=cost_result.rank,
                total_cost=cost_result.total_cost,
                cost_index=cost_result.cost_index,
                total_distance=cost_result.total_distance,
                start_pole_id=cost_result.start_pole_id,
                start_pole_coord=[cost_result.start_pole_coord[0], cost_result.start_pole_coord[1]],
                new_poles_count=cost_result.new_poles_count,
                path_coordinates=cost_result.path_coordinates,
                new_pole_coordinates=cost_result.new_pole_coordinates,
                wire_cost=cost_result.cost_breakdown.wire_cost,
                pole_cost=cost_result.cost_breakdown.pole_cost,
                labor_cost=cost_result.cost_breakdown.labor_cost,
                remark=cost_result.remark,
                detailed_cost=detailed_cost,
                voltage_drop=voltage_drop,
                pole_spec="C10",
                wire_spec="OW_22",
                source_voltage_type=source_voltage_type,
                source_phase_type=source_phase_type
            )
            routes.append(route)
        
        return routes
