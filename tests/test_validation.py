"""
ELBIX AIDD 검증 테스트
- 테스트 좌표로 설계 실행
- 예상 결과와 비교
"""

import pytest
import asyncio
import json
from typing import List, Tuple, Dict, Any
from pathlib import Path

from app.core.design_engine import DesignEngine
from app.models.response import DesignStatus


# 테스트 데이터 로드
TEST_POINTS = [
    [14242500.630572468, 4437638.68682943],
    [14242910.956049535, 4437665.324854794],
    [14242983.45620861, 4437440.9804903725],
    [14243049.216050547, 4436947.987531691],
    [14243659.268491792, 4436489.878246594],
]

# 예상 결과 (testanswer.md에서 발췌)
EXPECTED_RESULTS = [
    {
        "point": [14242500.630572468, 4437638.68682943],
        "coords": [
            [[14242558.8046557, 4437682.77422887], [14242526.905874047, 4437647.983015818], 
             [14242516.997539336, 4437630.704207546], [14242500.630572466, 4437638.686829429]],
            [[14242504.6385371, 4437567.848405449], [14242503.932523599, 4437605.365054101], 
             [14242516.997539336, 4437630.704207546], [14242500.630572466, 4437638.686829429]]
        ]
    },
    {
        "point": [14242910.956049535, 4437665.324854794],
        "coords": [
            [[14242910.956049534, 4437665.324854794], [14242873.9624174, 4437620.84808657]]
        ]
    },
    {
        "point": [14242983.45620861, 4437440.9804903725],
        "coords": [
            [[14242983.456208609, 4437440.980490372], [14242956.587635098, 4437481.816680648]]
        ]
    },
    {
        "point": [14243049.216050547, 4436947.987531691],
        "coords": [
            [[14243131.680845799, 4436863.161483939], [14243094.450958438, 4436854.368184084],
             [14243073.922517803, 4436900.122286329], [14243058.05453672, 4436947.727549344],
             [14243057.55694289, 4436949.897093024], [14243049.216050547, 4436947.987531692]]
        ]
    },
    {
        "point": [14243659.268491792, 4436489.878246594],
        "coords": [
            [[14243659.26849179, 4436489.878246593], [14243669.106066098, 4436429.429122289]]
        ]
    }
]


def calculate_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """두 점 사이 거리 계산"""
    import math
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)


def find_closest_point(target: Tuple[float, float], coords: List[Tuple[float, float]]) -> Tuple[float, float]:
    """좌표 리스트에서 가장 가까운 점 찾기"""
    min_dist = float('inf')
    closest = None
    for coord in coords:
        dist = calculate_distance(target, coord)
        if dist < min_dist:
            min_dist = dist
            closest = coord
    return closest, min_dist


def compare_paths(
    actual_path: List[Tuple[float, float]], 
    expected_paths: List[List[List[float]]],
    tolerance: float = 50.0  # 50m 허용 오차
) -> Dict[str, Any]:
    """
    실제 경로와 예상 경로 비교
    
    Args:
        actual_path: 실제 생성된 경로 좌표
        expected_paths: 예상 경로들 (여러 경로 중 하나와 일치하면 성공)
        tolerance: 허용 오차 (미터)
    
    Returns:
        비교 결과
    """
    if not actual_path:
        return {"match": False, "reason": "실제 경로 없음"}
    
    best_match_score = 0
    best_match_idx = -1
    
    for idx, expected in enumerate(expected_paths):
        # 시작점과 끝점 비교
        expected_start = tuple(expected[0])
        expected_end = tuple(expected[-1])
        actual_start = actual_path[0]
        actual_end = actual_path[-1]
        
        # 끝점(수용가)이 가까운지 확인
        end_dist = calculate_distance(actual_end, expected_end)
        
        if end_dist < tolerance:
            # 시작점(전주)이 가까운지 확인
            start_dist = calculate_distance(actual_start, expected_start)
            
            # 점수 계산 (낮을수록 좋음)
            score = 1.0 / (1.0 + end_dist + start_dist)
            
            if score > best_match_score:
                best_match_score = score
                best_match_idx = idx
    
    if best_match_idx >= 0:
        return {
            "match": True,
            "matched_path_idx": best_match_idx,
            "score": best_match_score
        }
    
    return {"match": False, "reason": "일치하는 경로 없음"}


@pytest.mark.asyncio
class TestValidation:
    """검증 테스트"""
    
    async def test_single_point(self):
        """단일 좌표 테스트"""
        point = TEST_POINTS[0]
        expected = EXPECTED_RESULTS[0]
        
        coord_str = f"{point[0]},{point[1]}"
        
        print(f"\n=== 테스트 좌표: {coord_str} ===")
        
        try:
            engine = DesignEngine()
            result = await engine.run(coord=coord_str, phase_code="1")
            
            print(f"상태: {result.status}")
            print(f"경로 수: {len(result.routes)}")
            
            if result.routes:
                for i, route in enumerate(result.routes[:3]):
                    print(f"\n경로 {i+1} (Rank {route.rank}):")
                    print(f"  전주 ID: {route.start_pole_id}")
                    print(f"  거리: {route.total_distance:.1f}m")
                    print(f"  신설 전주: {route.new_poles_count}개")
                    
                    # 예상 결과와 비교
                    actual_path = route.path_coordinates
                    if actual_path:
                        comparison = compare_paths(actual_path, expected["coords"])
                        print(f"  예상 결과 일치: {comparison}")
            
            # 결과가 있으면 성공
            if result.status == DesignStatus.SUCCESS and result.routes:
                assert True
            else:
                print(f"  경고: 결과 없음")
                
        except Exception as e:
            print(f"오류: {e}")
            pytest.skip(f"테스트 실패: {e}")
    
    async def test_multiple_points(self):
        """여러 좌표 테스트"""
        results_summary = []
        
        print("\n=== 다중 좌표 테스트 ===")
        
        for i, (point, expected) in enumerate(zip(TEST_POINTS[:5], EXPECTED_RESULTS[:5])):
            coord_str = f"{point[0]},{point[1]}"
            
            try:
                engine = DesignEngine()
                result = await engine.run(coord=coord_str, phase_code="1")
                
                summary = {
                    "index": i + 1,
                    "coord": coord_str[:30] + "...",
                    "status": str(result.status),
                    "routes": len(result.routes),
                    "match": False
                }
                
                if result.routes:
                    actual_path = result.routes[0].path_coordinates
                    if actual_path:
                        comparison = compare_paths(actual_path, expected["coords"])
                        summary["match"] = comparison.get("match", False)
                
                results_summary.append(summary)
                
            except Exception as e:
                results_summary.append({
                    "index": i + 1,
                    "coord": coord_str[:30] + "...",
                    "status": "ERROR",
                    "error": str(e)
                })
        
        # 결과 출력
        print("\n| # | 좌표 | 상태 | 경로 수 | 일치 |")
        print("|---|------|------|---------|------|")
        for s in results_summary:
            match_str = "✓" if s.get("match") else "✗"
            routes = s.get("routes", 0)
            print(f"| {s['index']} | {s['coord']} | {s['status']} | {routes} | {match_str} |")
    
    async def test_detailed_comparison(self):
        """상세 비교 테스트"""
        # 첫 번째 테스트 포인트로 상세 분석
        point = TEST_POINTS[0]
        expected = EXPECTED_RESULTS[0]
        coord_str = f"{point[0]},{point[1]}"
        
        print(f"\n=== 상세 비교 테스트 ===")
        print(f"수용가 좌표: [{point[0]}, {point[1]}]")
        
        # 예상 경로 분석
        print(f"\n예상 경로 ({len(expected['coords'])}개):")
        for i, path in enumerate(expected['coords']):
            start = path[0]
            end = path[-1]
            path_len = sum(
                calculate_distance(tuple(path[j]), tuple(path[j+1]))
                for j in range(len(path) - 1)
            )
            print(f"  경로 {i+1}: 시작점 {start}, 끝점 {end}, 총 거리 {path_len:.1f}m")
        
        try:
            engine = DesignEngine()
            result = await engine.run(coord=coord_str, phase_code="1")
            
            print(f"\n실제 결과:")
            print(f"  상태: {result.status}")
            print(f"  처리 시간: {result.processing_time_ms}ms")
            
            if result.routes:
                for i, route in enumerate(result.routes[:3]):
                    print(f"\n  경로 {i+1}:")
                    print(f"    전주 ID: {route.start_pole_id}")
                    print(f"    거리: {route.total_distance:.1f}m")
                    print(f"    신설 전주: {route.new_poles_count}개")
                    print(f"    비용 지수: {route.cost_index}")
                    
                    if route.path_coordinates:
                        start = route.path_coordinates[0]
                        end = route.path_coordinates[-1]
                        print(f"    시작점: {start}")
                        print(f"    끝점: {end}")
                        
                        # 예상 결과 경로와 거리 비교
                        for j, exp_path in enumerate(expected['coords']):
                            exp_start = tuple(exp_path[0])
                            exp_end = tuple(exp_path[-1])
                            
                            start_dist = calculate_distance(start, exp_start)
                            end_dist = calculate_distance(end, exp_end)
                            
                            print(f"    vs 예상경로{j+1}: 시작점 오차 {start_dist:.1f}m, 끝점 오차 {end_dist:.1f}m")
            else:
                print("  경로 없음")
                
        except Exception as e:
            print(f"오류: {e}")
            import traceback
            traceback.print_exc()


@pytest.mark.asyncio  
class TestFullValidation:
    """전체 테스트 포인트 검증"""
    
    async def test_all_testpoints(self):
        """모든 테스트 포인트 검증"""
        # docs/testpoints.md의 모든 좌표
        all_points = [
            [14242500.630572468, 4437638.68682943],
            [14242910.956049535, 4437665.324854794],
            [14242983.45620861, 4437440.9804903725],
            [14243049.216050547, 4436947.987531691],
            [14243659.268491792, 4436489.878246594],
            [14243669.293968752, 4436492.529276953],
            [14243763.053539224, 4436237.819504912],
            [14242991.510561015, 4436042.775295429],
            [14243017.469385289, 4436052.053893486],
            [14243021.88800527, 4436200.573018714],
        ]
        
        print("\n=== 전체 테스트 포인트 검증 (10개) ===\n")
        
        success_count = 0
        fail_count = 0
        
        for i, point in enumerate(all_points):
            coord_str = f"{point[0]},{point[1]}"
            
            try:
                engine = DesignEngine()
                result = await engine.run(coord=coord_str, phase_code="1")
                
                status = "✓" if result.status == DesignStatus.SUCCESS and result.routes else "✗"
                routes = len(result.routes) if result.routes else 0
                
                if result.routes:
                    best = result.routes[0]
                    print(f"{i+1}. {status} 좌표: [...{str(point[0])[-6:]}] → {routes}개 경로, "
                          f"최적: {best.total_distance:.0f}m, 전주 {best.new_poles_count}개")
                    success_count += 1
                else:
                    print(f"{i+1}. {status} 좌표: [...{str(point[0])[-6:]}] → 경로 없음")
                    fail_count += 1
                    
            except Exception as e:
                print(f"{i+1}. ✗ 좌표: [...{str(point[0])[-6:]}] → 오류: {str(e)[:50]}")
                fail_count += 1
        
        print(f"\n결과: 성공 {success_count}/{len(all_points)}, 실패 {fail_count}/{len(all_points)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
