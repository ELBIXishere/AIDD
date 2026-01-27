#!/usr/bin/env python3
"""
신설전주 배치 로직 검증 테스트
- 실제 좌표 데이터로 전주 배치 검증
- 분기점 추가 로직 검증
- 기설전주 근처 배치 제외 검증
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.pole_allocator import PoleAllocator
from app.core.pathfinder import PathResult
from typing import List, Tuple

def create_test_path_result(
    path_coords: List[Tuple[float, float]],
    total_distance: float,
    target_pole_id: str = "TEST_POLE_1"
) -> PathResult:
    """테스트용 PathResult 생성"""
    return PathResult(
        target_pole_id=target_pole_id,
        target_node_id=f"NODE_{target_pole_id}",
        target_coord=path_coords[-1] if path_coords else (0, 0),
        path_nodes=[f"NODE_{i}" for i in range(len(path_coords))],
        path_coords=path_coords,
        total_distance=total_distance,
        total_weight=total_distance,
        is_reachable=True,
        is_fast_track=False
    )

def test_pole_allocation_88_2m():
    """88.2m 경로 테스트 (경로 2 케이스)"""
    print("\n" + "="*60)
    print("테스트 1: 88.2m 경로 (직선 경로)")
    print("="*60)
    
    # 88.2m 직선 경로 생성 (수용가 → 기설전주)
    consumer_coord = (14242500.63, 4437638.69)
    # 기설전주 방향으로 88.2m 떨어진 위치
    import math
    # 간단히 X축 방향으로 88.2m 이동
    existing_pole_coord = (consumer_coord[0] + 88.2, consumer_coord[1])
    
    path_coords = [consumer_coord, existing_pole_coord]
    
    allocator = PoleAllocator()
    path_result = create_test_path_result(path_coords, 88.2)
    
    result = allocator.allocate(path_result)
    
    print(f"경로 길이: {path_result.total_distance:.1f}m")
    print(f"배치된 전주 수: {len(result.new_poles)}개")
    print(f"메시지: {result.message}")
    print("\n전주 배치 위치:")
    for i, pole in enumerate(result.new_poles, 1):
        print(f"  {i}. 위치: {pole.distance_from_consumer:.1f}m, "
              f"좌표: ({pole.coord[0]:.2f}, {pole.coord[1]:.2f}), "
              f"분기점: {pole.is_junction}")
    
    # 예상: 수용가(0m), 40m, 80m는 73.2m를 초과하므로 배치 안됨
    # 하지만 분기점이 있으면 추가될 수 있음
    expected_count = 2  # 0m, 40m
    if len(result.new_poles) > expected_count:
        print(f"\n⚠️  경고: 예상 전주 수({expected_count}개)보다 많음 ({len(result.new_poles)}개)")
        print("   분기점이 추가되었거나 로직에 문제가 있을 수 있습니다.")
    
    return result

def test_pole_allocation_with_junction():
    """분기점이 있는 경로 테스트"""
    print("\n" + "="*60)
    print("테스트 2: 분기점이 있는 경로")
    print("="*60)
    
    # 꺾이는 경로 생성 (분기점 포함)
    consumer_coord = (14242500.63, 4437638.69)
    mid_coord = (consumer_coord[0] + 40, consumer_coord[1] + 20)  # 40m 지점에서 꺾임
    existing_pole_coord = (mid_coord[0] + 50, mid_coord[1] + 10)  # 추가 50m
    
    path_coords = [consumer_coord, mid_coord, existing_pole_coord]
    
    allocator = PoleAllocator()
    # 실제 거리 계산
    from app.utils.coordinate import calculate_distance
    dist1 = calculate_distance(consumer_coord[0], consumer_coord[1], mid_coord[0], mid_coord[1])
    dist2 = calculate_distance(mid_coord[0], mid_coord[1], existing_pole_coord[0], existing_pole_coord[1])
    total_dist = dist1 + dist2
    
    path_result = create_test_path_result(path_coords, total_dist)
    
    result = allocator.allocate(path_result)
    
    print(f"경로 길이: {path_result.total_distance:.1f}m")
    print(f"유효 거리: {path_result.total_distance - allocator.MIN_DISTANCE_TO_EXISTING_POLE:.1f}m")
    print(f"배치된 전주 수: {len(result.new_poles)}개")
    print(f"굴절 횟수: {result.turn_count}회")
    print(f"메시지: {result.message}")
    print("\n전주 배치 위치:")
    for i, pole in enumerate(result.new_poles, 1):
        print(f"  {i}. 위치: {pole.distance_from_consumer:.1f}m, "
              f"분기점: {pole.is_junction}")
    
    return result

def test_pole_allocation_93_5m():
    """93.5m 경로 테스트 (경로 1 케이스)"""
    print("\n" + "="*60)
    print("테스트 3: 93.5m 경로 (직선 경로)")
    print("="*60)
    
    consumer_coord = (14242500.63, 4437638.69)
    existing_pole_coord = (consumer_coord[0] + 93.5, consumer_coord[1])
    
    path_coords = [consumer_coord, existing_pole_coord]
    
    allocator = PoleAllocator()
    path_result = create_test_path_result(path_coords, 93.5)
    
    result = allocator.allocate(path_result)
    
    print(f"경로 길이: {path_result.total_distance:.1f}m")
    print(f"배치된 전주 수: {len(result.new_poles)}개")
    print(f"메시지: {result.message}")
    print("\n전주 배치 위치:")
    for i, pole in enumerate(result.new_poles, 1):
        print(f"  {i}. 위치: {pole.distance_from_consumer:.1f}m")
    
    # 예상: 수용가(0m), 40m, 80m는 78.5m를 초과하므로 배치 안됨
    expected_count = 2  # 0m, 40m
    if len(result.new_poles) > expected_count:
        print(f"\n⚠️  경고: 예상 전주 수({expected_count}개)보다 많음 ({len(result.new_poles)}개)")
    
    return result

def analyze_pole_positions_logic():
    """전주 배치 로직 분석"""
    print("\n" + "="*60)
    print("로직 분석: _calculate_pole_positions")
    print("="*60)
    
    allocator = PoleAllocator()
    
    test_cases = [
        (88.2, "경로 2"),
        (93.5, "경로 1"),
        (100.0, "100m 경로"),
        (120.0, "120m 경로"),
    ]
    
    for total_length, name in test_cases:
        print(f"\n{name} ({total_length}m):")
        effective_length = total_length - allocator.MIN_DISTANCE_TO_EXISTING_POLE
        print(f"  - 유효 거리: {effective_length:.1f}m (총 {total_length}m - {allocator.MIN_DISTANCE_TO_EXISTING_POLE}m)")
        print(f"  - 전주 간격: {allocator.pole_interval}m")
        
        positions = []
        positions.append(0)  # 수용가 위치
        
        current_pos = allocator.pole_interval
        while current_pos <= effective_length:
            positions.append(current_pos)
            current_pos += allocator.pole_interval
        
        print(f"  - 배치 위치: {positions}")
        print(f"  - 예상 전주 수: {len(positions)}개")
        
        # 분기점이 추가되면 전주 수가 증가할 수 있음
        print(f"  - 참고: 분기점이 있으면 추가 전주 배치 가능")

if __name__ == "__main__":
    print("신설전주 배치 로직 검증 테스트 시작")
    print("="*60)
    
    # 로직 분석
    analyze_pole_positions_logic()
    
    # 실제 경로 테스트
    test_pole_allocation_88_2m()
    test_pole_allocation_93_5m()
    test_pole_allocation_with_junction()
    
def test_complex_path_multiple_junctions():
    """여러 분기점이 있는 복잡한 경로 테스트 (88.2m)"""
    print("\n" + "="*60)
    print("테스트 4: 여러 분기점이 있는 88.2m 경로")
    print("="*60)
    
    # 여러 번 꺾이는 경로 생성 (분기점 여러 개)
    consumer_coord = (14242500.63, 4437638.69)
    # 경로를 여러 세그먼트로 나눔
    coord1 = (consumer_coord[0] + 20, consumer_coord[1] + 5)   # 20m 지점
    coord2 = (coord1[0] + 20, coord1[1] - 5)                   # 40m 지점 (꺾임)
    coord3 = (coord2[0] + 20, coord2[1] + 5)                   # 60m 지점 (꺾임)
    existing_pole_coord = (coord3[0] + 28.2, coord3[1])        # 88.2m
    
    path_coords = [consumer_coord, coord1, coord2, coord3, existing_pole_coord]
    
    allocator = PoleAllocator()
    # 실제 거리 계산
    from app.utils.coordinate import calculate_distance
    total_dist = 0
    for i in range(len(path_coords) - 1):
        dist = calculate_distance(
            path_coords[i][0], path_coords[i][1],
            path_coords[i+1][0], path_coords[i+1][1]
        )
        total_dist += dist
    
    path_result = create_test_path_result(path_coords, total_dist)
    
    result = allocator.allocate(path_result)
    
    print(f"경로 길이: {path_result.total_distance:.1f}m")
    print(f"유효 거리: {path_result.total_distance - allocator.MIN_DISTANCE_TO_EXISTING_POLE:.1f}m")
    print(f"배치된 전주 수: {len(result.new_poles)}개")
    print(f"굴절 횟수: {result.turn_count}회")
    print(f"메시지: {result.message}")
    print("\n전주 배치 위치:")
    for i, pole in enumerate(result.new_poles, 1):
        print(f"  {i}. 위치: {pole.distance_from_consumer:.1f}m, "
              f"분기점: {pole.is_junction}")
    
    if len(result.new_poles) > 2:
        print(f"\n⚠️  경고: 88.2m 경로에서 {len(result.new_poles)}개 전주가 배치됨")
        print("   분기점이 추가되어 전주 수가 증가했습니다.")
    
    return result

if __name__ == "__main__":
    print("신설전주 배치 로직 검증 테스트 시작")
    print("="*60)
    
    # 로직 분석
    analyze_pole_positions_logic()
    
    # 실제 경로 테스트
    test_pole_allocation_88_2m()
    test_pole_allocation_93_5m()
    test_pole_allocation_with_junction()
    test_complex_path_multiple_junctions()
    
    print("\n" + "="*60)
    print("테스트 완료")
    print("="*60)
