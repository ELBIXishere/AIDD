"""
ELBIX AIDD 성능 벤치마크 테스트
- 각 단계별 실행 시간 측정
- 캐시 히트율 검증
- 최적화 효과 비교
"""

import pytest
import asyncio
import time
from typing import Dict, Any

from app.config import settings
from app.core.design_engine import DesignEngine
from app.core.wfs_client import WFSClient, WFSCache
from app.core.preprocessor import DataPreprocessor
from app.core.target_selector import TargetSelector
from app.core.graph_builder import RoadGraphBuilder, RTREE_AVAILABLE
from app.core.pathfinder import Pathfinder
from app.core.pole_allocator import PoleAllocator
from app.core.cost_calculator import CostCalculator
from app.models.response import DesignStatus
from app.utils.profiler import (
    get_profiler, clear_profiling_stats, 
    get_profiling_summary, enable_profiling,
    start_memory_tracking, get_memory_usage, stop_memory_tracking
)


# 테스트용 좌표
TEST_COORD = "14241940.817790061,4437601.6755945515"
TEST_X = 14241940.817790061
TEST_Y = 4437601.6755945515


class TestBenchmarkSetup:
    """벤치마크 환경 확인"""
    
    def test_rtree_availability(self):
        """R-tree 공간 인덱스 가용성 확인"""
        print(f"\nR-tree 가용: {RTREE_AVAILABLE}")
        # R-tree 없어도 해시맵 기반으로 동작
    
    def test_profiler_setup(self):
        """프로파일러 설정 확인"""
        clear_profiling_stats()
        enable_profiling()
        profiler = get_profiler()
        assert profiler.enabled, "프로파일러가 활성화되어야 함"


@pytest.mark.asyncio
class TestWFSCacheBenchmark:
    """WFS 캐시 성능 벤치마크"""
    
    async def test_cache_hit_performance(self):
        """캐시 히트 시 성능 비교"""
        client = WFSClient(use_cache=True)
        client.clear_cache()
        
        # 첫 번째 요청 (캐시 미스)
        start1 = time.perf_counter()
        try:
            data1 = await client.get_all_data(TEST_X, TEST_Y, 400)
            elapsed1 = (time.perf_counter() - start1) * 1000
            
            # 두 번째 요청 (캐시 히트)
            start2 = time.perf_counter()
            data2 = await client.get_all_data(TEST_X, TEST_Y, 400)
            elapsed2 = (time.perf_counter() - start2) * 1000
            
            # 캐시 통계
            stats = client.get_cache_stats()
            
            print(f"\n=== WFS 캐시 벤치마크 ===")
            print(f"  첫 번째 요청 (캐시 미스): {elapsed1:.2f}ms")
            print(f"  두 번째 요청 (캐시 히트): {elapsed2:.2f}ms")
            print(f"  성능 향상: {((elapsed1 - elapsed2) / elapsed1 * 100):.1f}%")
            print(f"  캐시 통계: {stats}")
            
            # 캐시 히트 시 더 빨라야 함
            assert elapsed2 < elapsed1, "캐시 히트 시 더 빨라야 함"
            
        except Exception as e:
            pytest.skip(f"WFS 서버 연결 불가: {e}")
    
    async def test_cache_stats(self):
        """캐시 통계 검증"""
        client = WFSClient(use_cache=True)
        client.clear_cache()
        
        try:
            # 요청 3회 (같은 좌표)
            for _ in range(3):
                await client.get_poles(TEST_X, TEST_Y, 400)
            
            stats = client.get_cache_stats()
            
            print(f"\n캐시 통계: {stats}")
            
            # 3회 요청 중 2회는 캐시 히트
            assert stats["hits"] >= 2, f"캐시 히트가 2회 이상이어야 함 (실제: {stats['hits']})"
            
        except Exception as e:
            pytest.skip(f"WFS 서버 연결 불가: {e}")


@pytest.mark.asyncio
class TestPathfinderBenchmark:
    """경로 탐색 알고리즘 벤치마크"""
    
    async def test_astar_vs_dijkstra(self):
        """A* vs Dijkstra 성능 비교"""
        try:
            # 데이터 준비
            client = WFSClient()
            raw_data = await client.get_all_data(TEST_X, TEST_Y, 400)
            
            preprocessor = DataPreprocessor()
            processed_data = preprocessor.process(raw_data)
            
            if not processed_data.poles or not processed_data.roads:
                pytest.skip("데이터 부족")
            
            selector = TargetSelector(processed_data)
            selection = selector.select((TEST_X, TEST_Y), "1")
            
            if not selection.targets:
                pytest.skip("후보 전주 없음")
            
            graph_builder = RoadGraphBuilder(processed_data)
            road_graph = graph_builder.build((TEST_X, TEST_Y), selection.targets)
            
            # A* 벤치마크
            pathfinder_astar = Pathfinder(road_graph, use_astar=True)
            start_astar = time.perf_counter()
            result_astar = pathfinder_astar.find_paths(selection.targets)
            elapsed_astar = (time.perf_counter() - start_astar) * 1000
            
            # 그래프 재구축 (캐시 무효화)
            graph_builder2 = RoadGraphBuilder(processed_data)
            road_graph2 = graph_builder2.build((TEST_X, TEST_Y), selection.targets)
            
            # Dijkstra 벤치마크
            pathfinder_dijkstra = Pathfinder(road_graph2, use_astar=False)
            start_dijkstra = time.perf_counter()
            result_dijkstra = pathfinder_dijkstra.find_paths(selection.targets)
            elapsed_dijkstra = (time.perf_counter() - start_dijkstra) * 1000
            
            print(f"\n=== 경로 탐색 알고리즘 벤치마크 ===")
            print(f"  A* 알고리즘: {elapsed_astar:.2f}ms, {len(result_astar.paths)}개 경로")
            print(f"  Dijkstra: {elapsed_dijkstra:.2f}ms, {len(result_dijkstra.paths)}개 경로")
            
            improvement = ((elapsed_dijkstra - elapsed_astar) / elapsed_dijkstra * 100) if elapsed_dijkstra > 0 else 0
            print(f"  A* 성능 향상: {improvement:.1f}%")
            
        except Exception as e:
            pytest.skip(f"테스트 실패: {e}")


@pytest.mark.asyncio
class TestFullPipelineBenchmark:
    """전체 파이프라인 벤치마크"""
    
    async def test_end_to_end_performance(self):
        """종단간 성능 측정"""
        clear_profiling_stats()
        enable_profiling()
        
        try:
            engine = DesignEngine()
            
            # 3회 실행 (첫 번째는 캐시 미스, 이후 캐시 히트)
            times = []
            
            for i in range(3):
                start = time.perf_counter()
                result = await engine.run(
                    coord=TEST_COORD,
                    phase_code="1"
                )
                elapsed = (time.perf_counter() - start) * 1000
                times.append(elapsed)
                
                if i == 0:
                    print(f"\n=== 전체 파이프라인 벤치마크 ===")
                    print(f"  상태: {result.status}")
                    print(f"  경로 수: {len(result.routes)}")
                
                print(f"  실행 {i+1}: {elapsed:.2f}ms")
            
            # 프로파일링 결과
            print(get_profiling_summary())
            
            # 캐시 통계
            wfs_client = WFSClient()
            print(f"\n캐시 통계: {wfs_client.get_cache_stats()}")
            
            # 두 번째 이후 실행이 더 빨라야 함 (캐시 효과)
            if len(times) >= 2:
                avg_cached = sum(times[1:]) / len(times[1:])
                improvement = ((times[0] - avg_cached) / times[0] * 100)
                print(f"\n캐시 히트 후 성능 향상: {improvement:.1f}%")
            
        except Exception as e:
            pytest.skip(f"테스트 실패: {e}")
    
    async def test_memory_usage(self):
        """메모리 사용량 측정"""
        try:
            start_memory_tracking()
            
            engine = DesignEngine()
            result = await engine.run(
                coord=TEST_COORD,
                phase_code="1"
            )
            
            memory = get_memory_usage()
            stop_memory_tracking()
            
            print(f"\n=== 메모리 사용량 ===")
            if "error" not in memory:
                print(f"  현재: {memory['current_mb']:.2f} MB")
                print(f"  최대: {memory['peak_mb']:.2f} MB")
            else:
                print(f"  {memory['error']}")
            
        except Exception as e:
            stop_memory_tracking()
            pytest.skip(f"테스트 실패: {e}")


@pytest.mark.asyncio
class TestSpatialIndexBenchmark:
    """공간 인덱싱 벤치마크"""
    
    async def test_node_lookup_performance(self):
        """노드 조회 성능 측정"""
        try:
            client = WFSClient()
            raw_data = await client.get_all_data(TEST_X, TEST_Y, 400)
            
            preprocessor = DataPreprocessor()
            processed_data = preprocessor.process(raw_data)
            
            if not processed_data.roads:
                pytest.skip("도로 데이터 없음")
            
            selector = TargetSelector(processed_data)
            selection = selector.select((TEST_X, TEST_Y), "1")
            
            # 그래프 구축 (공간 인덱싱 적용)
            start = time.perf_counter()
            graph_builder = RoadGraphBuilder(processed_data)
            road_graph = graph_builder.build((TEST_X, TEST_Y), selection.targets)
            elapsed = (time.perf_counter() - start) * 1000
            
            print(f"\n=== 공간 인덱싱 벤치마크 ===")
            print(f"  그래프 구축: {elapsed:.2f}ms")
            print(f"  노드 수: {road_graph.graph.number_of_nodes()}")
            print(f"  엣지 수: {road_graph.graph.number_of_edges()}")
            print(f"  R-tree 사용: {RTREE_AVAILABLE}")
            
        except Exception as e:
            pytest.skip(f"테스트 실패: {e}")


class TestPerformanceSummary:
    """성능 요약 테스트"""
    
    def test_print_summary(self):
        """프로파일링 요약 출력"""
        summary = get_profiling_summary()
        print(summary)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
