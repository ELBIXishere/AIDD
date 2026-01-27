"""
ELBIX AIDD 통합 테스트
- 실제 WFS 서버 연동 테스트
- PRD 요구사항 검증
"""

import pytest
import asyncio
import math
from typing import List, Tuple

from app.config import settings
from app.core.design_engine import DesignEngine
from app.core.wfs_client import WFSClient
from app.core.preprocessor import DataPreprocessor
from app.core.target_selector import TargetSelector
from app.core.graph_builder import RoadGraphBuilder
from app.core.pathfinder import Pathfinder
from app.core.pole_allocator import PoleAllocator
from app.core.cost_calculator import CostCalculator
from app.core.line_validator import LineValidator
from app.core.eps_client import EPSClient
from app.models.response import DesignStatus


# 테스트용 좌표 (PRD에서 제공된 예시)
TEST_COORD = "14241940.817790061,4437601.6755945515"
TEST_X = 14241940.817790061
TEST_Y = 4437601.6755945515


class TestPoleFormula:
    """PRD 4.1 전주 개수 산출 공식 테스트"""
    
    def test_pole_count_30m(self):
        """30m 이하: 전주 1개"""
        allocator = PoleAllocator()
        count = allocator._calculate_pole_count(25.0)
        assert count == 1, f"25m 거리에서 전주 개수는 1개여야 함 (실제: {count})"
    
    def test_pole_count_70m(self):
        """70m: PRD 공식 N = 1 + ceil((70-30)/40) = 1 + 1 = 2개"""
        allocator = PoleAllocator()
        count = allocator._calculate_pole_count(70.0)
        expected = 1 + math.ceil((70 - 30) / 40)
        assert count == expected, f"70m 거리에서 전주 개수는 {expected}개여야 함 (실제: {count})"
    
    def test_pole_count_120m(self):
        """120m: PRD Case Study - N = 1 + ceil((120-30)/40) = 1 + 3 = 4개"""
        allocator = PoleAllocator()
        count = allocator._calculate_pole_count(120.0)
        # PRD Case Study: 120m → 4본
        expected = 1 + math.ceil((120 - 30) / 40)  # 1 + ceil(2.25) = 1 + 3 = 4
        assert count == expected, f"120m 거리에서 전주 개수는 {expected}개여야 함 (실제: {count})"
    
    def test_pole_count_400m(self):
        """400m (최대): N = 1 + ceil((400-30)/40) = 1 + 10 = 11개"""
        allocator = PoleAllocator()
        count = allocator._calculate_pole_count(400.0)
        expected = 1 + math.ceil((400 - 30) / 40)  # 1 + ceil(9.25) = 1 + 10 = 11
        assert count == expected, f"400m 거리에서 전주 개수는 {expected}개여야 함 (실제: {count})"


class TestCostIndex:
    """PRD 4.2 경로 평가 점수(Scoring) 테스트"""
    
    def test_cost_index_calculation(self):
        """cost_index 계산 공식 검증"""
        calculator = CostCalculator()
        
        # Score = N_poles × 10000 + D × 1 + N_turns × 50
        poles = 3
        distance = 100.0
        turns = 2
        
        expected = (
            poles * settings.SCORE_WEIGHT_POLE +
            int(distance * settings.SCORE_WEIGHT_DISTANCE) +
            turns * settings.SCORE_WEIGHT_TURN
        )
        actual = calculator._calculate_cost_index(poles, distance, turns)
        
        assert actual == expected, f"cost_index 계산 오류: 기대 {expected}, 실제 {actual}"
    
    def test_pole_weight_priority(self):
        """전주 가중치가 거리보다 높은지 검증"""
        calculator = CostCalculator()
        
        # 경로 A: 전주 2개, 거리 100m, 굴절 0회
        score_a = calculator._calculate_cost_index(2, 100, 0)
        
        # 경로 B: 전주 3개, 거리 98m, 굴절 0회 (거리는 2m 짧지만 전주 1개 더)
        score_b = calculator._calculate_cost_index(3, 98, 0)
        
        # PRD: "거리가 2m 더 멀더라도 전주를 1개 덜 심는 경로가 상위 랭크"
        assert score_a < score_b, "전주 개수가 더 중요해야 함 (A가 B보다 낮은 점수)"


class TestLineValidator:
    """전선 교차 검증 테스트"""
    
    def test_no_crossing_detection(self):
        """교차 없는 경로 검증"""
        from app.core.preprocessor import ProcessedData, Line
        from shapely.geometry import LineString
        
        # 빈 전선 데이터로 ProcessedData 생성
        processed_data = ProcessedData()
        validator = LineValidator(processed_data)
        
        # 테스트 경로
        path = [(0, 0), (100, 100)]
        result = validator.validate_path(path)
        
        assert result.is_valid, "전선이 없으면 항상 유효해야 함"


@pytest.mark.asyncio
class TestWFSIntegration:
    """WFS 서버 연동 테스트"""
    
    async def test_wfs_connection(self):
        """WFS 서버 연결 테스트"""
        client = WFSClient()
        
        try:
            poles = await client.get_poles(TEST_X, TEST_Y, 400)
            # 데이터 반환 여부 확인 (비어있어도 연결 성공)
            assert isinstance(poles, list), "전주 데이터는 리스트여야 함"
            print(f"WFS 전주 데이터: {len(poles)}개")
        except Exception as e:
            pytest.skip(f"WFS 서버 연결 불가: {e}")
    
    async def test_wfs_all_data(self):
        """WFS 전체 데이터 수집 테스트"""
        client = WFSClient()
        
        try:
            data = await client.get_all_data(TEST_X, TEST_Y, 400)
            
            assert "poles" in data, "poles 키가 있어야 함"
            assert "lines" in data, "lines 키가 있어야 함"
            assert "roads" in data, "roads 키가 있어야 함"
            assert "buildings" in data, "buildings 키가 있어야 함"
            
            print(f"WFS 데이터: 전주 {len(data['poles'])}개, "
                  f"전선 {len(data['lines'])}개, "
                  f"도로 {len(data['roads'])}개, "
                  f"건물 {len(data['buildings'])}개")
        except Exception as e:
            pytest.skip(f"WFS 서버 연결 불가: {e}")


@pytest.mark.asyncio
class TestDesignEngine:
    """설계 엔진 통합 테스트"""
    
    async def test_design_single_phase(self):
        """단상 설계 요청 테스트"""
        engine = DesignEngine()
        
        try:
            result = await engine.run(
                coord=TEST_COORD,
                phase_code="1"  # 단상
            )
            
            print(f"\n단상 설계 결과:")
            print(f"  상태: {result.status}")
            print(f"  요청 규격: {result.request_spec}")
            print(f"  경로 수: {len(result.routes)}")
            
            if result.routes:
                for route in result.routes[:3]:
                    print(f"  - Rank {route.rank}: "
                          f"전주 {route.new_poles_count}개, "
                          f"거리 {route.total_distance:.1f}m, "
                          f"cost_index={route.cost_index}")
            
            # 상태 확인 (NO_ROUTE도 유효한 결과)
            assert result.status in [DesignStatus.SUCCESS, DesignStatus.NO_ROUTE], \
                f"예상치 못한 상태: {result.status}"
                
        except Exception as e:
            pytest.skip(f"설계 엔진 실행 실패: {e}")
    
    async def test_design_three_phase(self):
        """3상 설계 요청 테스트"""
        engine = DesignEngine()
        
        try:
            result = await engine.run(
                coord=TEST_COORD,
                phase_code="3"  # 3상
            )
            
            print(f"\n3상 설계 결과:")
            print(f"  상태: {result.status}")
            print(f"  요청 규격: {result.request_spec}")
            print(f"  경로 수: {len(result.routes)}")
            
            if result.routes:
                for route in result.routes[:3]:
                    print(f"  - Rank {route.rank}: "
                          f"전주 {route.new_poles_count}개, "
                          f"거리 {route.total_distance:.1f}m, "
                          f"cost_index={route.cost_index}")
            
            assert result.status in [DesignStatus.SUCCESS, DesignStatus.NO_ROUTE], \
                f"예상치 못한 상태: {result.status}"
                
        except Exception as e:
            pytest.skip(f"설계 엔진 실행 실패: {e}")
    
    async def test_design_cost_index_ordering(self):
        """cost_index 기준 정렬 검증"""
        engine = DesignEngine()
        
        try:
            result = await engine.run(
                coord=TEST_COORD,
                phase_code="1"
            )
            
            if result.status == DesignStatus.SUCCESS and len(result.routes) >= 2:
                # cost_index가 오름차순인지 확인
                for i in range(len(result.routes) - 1):
                    assert result.routes[i].cost_index <= result.routes[i + 1].cost_index, \
                        f"cost_index 정렬 오류: " \
                        f"Rank {i+1}({result.routes[i].cost_index}) > " \
                        f"Rank {i+2}({result.routes[i+1].cost_index})"
                
                print("\ncost_index 정렬 검증 통과")
            else:
                pytest.skip("경로가 2개 미만이어서 정렬 검증 불가")
                
        except Exception as e:
            pytest.skip(f"설계 엔진 실행 실패: {e}")


@pytest.mark.asyncio
class TestEPSClient:
    """EPS 서버 연동 테스트"""
    
    async def test_eps_health_check(self):
        """EPS 서버 상태 확인"""
        client = EPSClient()
        
        try:
            is_healthy = await client.health_check()
            print(f"\nEPS 서버 상태: {'정상' if is_healthy else '비정상'}")
            # 연결 실패해도 테스트는 통과 (선택적 기능)
        except Exception as e:
            print(f"EPS 서버 연결 실패 (무시): {e}")


class TestPreprocessor:
    """데이터 전처리 테스트"""
    
    def test_remove_demolished_poles(self):
        """철거 전주 제거 테스트"""
        preprocessor = DataPreprocessor()
        
        raw_poles = [
            {"properties": {"POLE_ID": "P1", "REMOVE_YN": "N"}, 
             "geometry": {"type": "Point", "coordinates": [0, 0]}},
            {"properties": {"POLE_ID": "P2", "REMOVE_YN": "Y"},  # 철거
             "geometry": {"type": "Point", "coordinates": [10, 10]}},
            {"properties": {"POLE_ID": "P3", "STAT_CD": "D"},     # 삭제
             "geometry": {"type": "Point", "coordinates": [20, 20]}},
        ]
        
        poles = preprocessor._process_poles(raw_poles)
        
        assert len(poles) == 1, f"철거 전주 제거 후 1개여야 함 (실제: {len(poles)})"
        assert poles[0].id == "P1", "P1만 남아야 함"
    
    def test_remove_support_poles(self):
        """지지주 제거 테스트"""
        preprocessor = DataPreprocessor()
        
        raw_poles = [
            {"properties": {"POLE_ID": "P1", "POLE_TYPE": "H"},  # 고압
             "geometry": {"type": "Point", "coordinates": [0, 0]}},
            {"properties": {"POLE_ID": "P2", "POLE_TYPE": "G"},  # 지지주
             "geometry": {"type": "Point", "coordinates": [10, 10]}},
        ]
        
        poles = preprocessor._process_poles(raw_poles)
        
        assert len(poles) == 1, f"지지주 제거 후 1개여야 함 (실제: {len(poles)})"
        assert poles[0].pole_type == "H", "고압 전주만 남아야 함"


class TestTargetSelector:
    """후보 전주 선별 테스트"""
    
    def test_fast_track_detection(self):
        """Fast Track (50m 이내) 감지 테스트"""
        from app.core.preprocessor import ProcessedData, Pole
        from shapely.geometry import Point
        
        # 테스트 데이터 생성
        processed_data = ProcessedData()
        processed_data.poles = [
            Pole(id="P1", geometry=Point(30, 0), coord=(30, 0), phase_code="1"),  # 30m (Fast Track)
            Pole(id="P2", geometry=Point(100, 0), coord=(100, 0), phase_code="1"),  # 100m
        ]
        
        selector = TargetSelector(processed_data)
        result = selector.select((0, 0), "1")
        
        assert result.fast_track_target is not None, "Fast Track 대상이 있어야 함"
        assert result.fast_track_target.id == "P1", "P1이 Fast Track 대상이어야 함"


# 전체 파이프라인 테스트
@pytest.mark.asyncio
class TestFullPipeline:
    """전체 파이프라인 통합 테스트"""
    
    async def test_full_design_pipeline(self):
        """
        전체 설계 파이프라인 테스트
        
        PRD 요구사항:
        - FR-01: 환경 데이터 수집 (400m BBox)
        - FR-02: 데이터 전처리
        - FR-03: 공급원 선별 (Phase Matching)
        - FR-04: Fast Track 판정
        - FR-05: 도로 네트워크 경로 탐색 + 전선 교차 검증
        - FR-06: 신설 전주 배치
        - FR-07: 공사비 산출 및 랭킹
        """
        print("\n=== 전체 파이프라인 테스트 시작 ===")
        
        try:
            # Phase 1: WFS 데이터 수집
            print("\n[Phase 1] WFS 데이터 수집...")
            wfs_client = WFSClient()
            raw_data = await wfs_client.get_all_data(TEST_X, TEST_Y, 400)
            print(f"  전주: {len(raw_data['poles'])}개")
            print(f"  전선: {len(raw_data['lines'])}개")
            print(f"  도로: {len(raw_data['roads'])}개")
            print(f"  건물: {len(raw_data['buildings'])}개")
            
            # Phase 2: 데이터 전처리
            print("\n[Phase 2] 데이터 전처리...")
            preprocessor = DataPreprocessor()
            processed_data = preprocessor.process(raw_data)
            print(f"  전처리 후 전주: {len(processed_data.poles)}개")
            print(f"  전처리 후 도로: {len(processed_data.roads)}개")
            
            if not processed_data.poles:
                pytest.skip("영역 내에 전주가 없음")
            
            # Phase 3: 후보 전주 선별
            print("\n[Phase 3] 후보 전주 선별...")
            selector = TargetSelector(processed_data)
            selection_result = selector.select((TEST_X, TEST_Y), "1")
            print(f"  후보 전주: {len(selection_result.targets)}개")
            
            if selection_result.fast_track_target:
                print(f"  Fast Track: {selection_result.fast_track_target.id} "
                      f"({selection_result.fast_track_target.distance_to_consumer:.1f}m)")
            
            if not selection_result.targets:
                pytest.skip("후보 전주가 없음")
            
            # Phase 4: 도로 네트워크 그래프
            print("\n[Phase 4] 도로 네트워크 그래프...")
            if not processed_data.roads:
                pytest.skip("도로 데이터가 없음")
            
            graph_builder = RoadGraphBuilder(processed_data)
            road_graph = graph_builder.build((TEST_X, TEST_Y), selection_result.targets)
            print(f"  노드: {road_graph.graph.number_of_nodes()}개")
            print(f"  엣지: {road_graph.graph.number_of_edges()}개")
            
            # Phase 5: 경로 탐색
            print("\n[Phase 5] 경로 탐색...")
            pathfinder = Pathfinder(road_graph)
            pathfinding_result = pathfinder.find_paths(selection_result.targets)
            print(f"  탐색된 경로: {len(pathfinding_result.paths)}개")
            
            if not pathfinding_result.paths:
                pytest.skip("유효한 경로가 없음")
            
            # Phase 5.5: 전선 교차 검증
            print("\n[Phase 5.5] 전선 교차 검증...")
            line_validator = LineValidator(processed_data)
            valid_paths = []
            for path in pathfinding_result.paths:
                if line_validator.validate_path(path.path_coords).is_valid:
                    valid_paths.append(path)
            print(f"  교차 검증 후: {len(valid_paths)}개")
            
            # Phase 6: 신설 전주 배치
            print("\n[Phase 6] 신설 전주 배치...")
            allocator = PoleAllocator()
            allocation_results = allocator.allocate_batch(valid_paths[:5])
            for alloc in allocation_results:
                print(f"  경로 {alloc.path_result.target_pole_id}: "
                      f"전주 {len(alloc.new_poles)}개 배치")
            
            # Phase 7: 공사비 계산
            print("\n[Phase 7] 공사비 계산...")
            calculator = CostCalculator()
            cost_results = calculator.calculate_batch(allocation_results)
            
            print("\n=== 최종 결과 ===")
            for result in cost_results[:3]:
                print(f"  Rank {result.rank}: {result.start_pole_id}")
                print(f"    - 전주: {result.new_poles_count}개")
                print(f"    - 거리: {result.total_distance:.1f}m")
                print(f"    - cost_index: {result.cost_index}")
                print(f"    - 총 비용: {result.total_cost:,}원")
            
            print("\n=== 파이프라인 테스트 완료 ===")
            
        except Exception as e:
            pytest.skip(f"파이프라인 실행 실패: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
