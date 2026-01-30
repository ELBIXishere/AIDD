import asyncio
import logging
from app.core.design_engine import DesignEngine
from app.config import settings
from app.utils.coordinate import calculate_distance
from app.core.pathfinder import PathResult

# 로깅 설정
logging.basicConfig(level=logging.INFO)

async def debug_cost():
    print("--- [비용 비교 분석] 단상(1상) 설계 시 왜 먼 전주가 선택되는가? ---")
    
    coord_consumer = (14242588.22, 4432200.94)
    coord_near_a = (14242679.12, 4432246.63) # A (Near)
    coord_far_b = (14242646.05, 4432049.70)  # B (Far)
    
    engine = DesignEngine()
    
    print("\n1. 데이터 준비 중...")
    raw_data = await engine.wfs_client.get_all_data(coord_consumer[0], coord_consumer[1], settings.BBOX_SIZE)
    from app.core.preprocessor import DataPreprocessor
    processed = DataPreprocessor().process(raw_data)
    
    # 전주 객체 찾기
    def get_pole(target_coord):
        min_d = float('inf')
        best = None
        for p in processed.poles:
            d = calculate_distance(target_coord[0], target_coord[1], p.coord[0], p.coord[1])
            if d < min_d:
                min_d = d
                best = p
        return best, min_d

    pole_a, dist_a = get_pole(coord_near_a)
    pole_b, dist_b = get_pole(coord_far_b)
    
    if not pole_a or not pole_b:
        print("전주를 찾지 못해 종료")
        return

    print(f"\n2. 타겟 전주 정보")
    print(f"  [A: 가까운 전주] ID={pole_a.id}, 직선거리={dist_a:.1f}m (실거리 ~96m)")
    print(f"  [B: 먼 전주]    ID={pole_b.id}, 직선거리={dist_b:.1f}m (실거리 ~162m)")

    # 그래프 및 경로 탐색
    print("\n3. 경로 탐색 및 공사비 산출 시뮬레이션 (단상 기준)")
    from app.core.graph_builder import RoadGraphBuilder
    from app.core.pathfinder import Pathfinder
    from app.core.pole_allocator import PoleAllocator
    from app.core.cost_calculator import CostCalculator
    from app.core.target_selector import TargetPole

    # 그래프 생성
    targets = [
        TargetPole(pole=pole_a, distance_to_consumer=96.0),
        TargetPole(pole=pole_b, distance_to_consumer=162.0)
    ]
    graph_builder = RoadGraphBuilder(processed)
    road_graph = graph_builder.build(coord_consumer, targets)
    
    pathfinder = Pathfinder(road_graph)
    allocator = PoleAllocator()
    calculator = CostCalculator(detailed_mode=True)

    # A, B 각각에 대해 계산
    for target in targets:
        label = "A (Near)" if target.pole.id == pole_a.id else "B (Far)"
        print(f"\n  >>> 시뮬레이션: {label} <<<")
        
        # 1) 경로 탐색
        pole_node_id = f"POLE_{target.pole.id}"
        path_result = pathfinder._astar_path(
            road_graph.consumer_node_id, 
            pole_node_id, 
            target
        )
        
        if not path_result or not path_result.is_reachable:
            print("      경로 생성 실패 (도달 불가)")
            continue
            
        print(f"      - 경로 거리: {path_result.total_distance:.1f}m")
        
        # 2) 전주 배치
        allocation = allocator.allocate(path_result)
        print(f"      - 신설 전주: {len(allocation.new_poles)}본")
        
        # 3) 공사비 계산
        cost_res = calculator.calculate(allocation)
        breakdown = cost_res.detailed_breakdown
        
        print(f"      - [총 공사비]: {breakdown.total_cost:,}원")
        print(f"        > 자재비: {breakdown.material.total:,}원 (전주 {breakdown.material.pole_cost:,} + 전선 {breakdown.material.wire_cost:,})")
        print(f"        > 노무비: {breakdown.labor.total:,}원")
        if breakdown.extra_cost > 0:
            print(f"        > 추가비용: {breakdown.extra_cost:,}원 ({breakdown.extra_detail})")
        
        # 점수 (Cost Index)
        print(f"      - [PRD 평가 점수]: {cost_res.cost_index}점 (낮을수록 좋음)")

if __name__ == "__main__":
    asyncio.run(debug_cost())
