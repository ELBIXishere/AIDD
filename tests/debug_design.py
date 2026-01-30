import asyncio
import logging
from app.core.design_engine import DesignEngine
from app.config import settings

# 로깅 설정
logging.basicConfig(level=logging.INFO)

async def test_design():
    print("--- 설계 엔진 디버깅 시작 ---")
    
    # 충주 지역 테스트 좌표 (도로 근처)
    coord = "14242500,4432200"
    phase = "1"
    
    engine = DesignEngine()
    
    # 1. WFS 데이터 수집 테스트
    print(f"\n[1. 데이터 수집] 좌표: {coord}")
    x, y = map(float, coord.split(','))
    raw_data = await engine.wfs_client.get_all_data(x, y, settings.BBOX_SIZE)
    
    print(f"  - Poles: {len(raw_data['poles'])}")
    print(f"  - Lines HV: {len(raw_data['lines_hv'])}")
    print(f"  - Lines LV: {len(raw_data['lines_lv'])}")
    print(f"  - Roads: {len(raw_data['roads'])}")
    
    if not raw_data['poles']:
        print("!!! 전주 데이터 없음 !!!")
        return

    # 2. 전처리 테스트
    print("\n[2. 전처리]")
    from app.core.preprocessor import DataPreprocessor
    preprocessor = DataPreprocessor()
    processed = preprocessor.process(raw_data)
    print(f"  - Processed Poles: {len(processed.poles)}")
    print(f"  - Processed Lines: {len(processed.lines)}")
    
    # 3. 후보 선별 테스트
    print("\n[3. 후보 선별]")
    from app.core.target_selector import TargetSelector
    selector = TargetSelector(processed)
    selection = selector.select((x, y), phase)
    print(f"  - Candidates: {len(selection.targets)}")
    if not selection.targets:
        print("!!! 후보 전주 없음 !!!")
        return

    # 4. 그래프 구축 테스트
    print("\n[4. 그래프 구축]")
    from app.core.graph_builder import RoadGraphBuilder
    builder = RoadGraphBuilder(processed)
    graph = builder.build((x, y), selection.targets)
    print(f"  - Nodes: {len(graph.nodes)}")
    print(f"  - Edges: {graph.graph.number_of_edges()}")
    print(f"  - Pole Nodes: {len(graph.pole_node_ids)}")
    
    if not graph.pole_node_ids:
        print("!!! 전주가 도로와 연결되지 않음 (Graph Empty) !!!")
        return

    # 5. 경로 탐색 테스트
    print("\n[5. 경로 탐색]")
    from app.core.pathfinder import Pathfinder
    pathfinder = Pathfinder(graph)
    paths = pathfinder.find_paths(selection.targets)
    print(f"  - Paths Found: {len(paths.paths)}")
    
    if paths.paths:
        print(f"  - Best Path Cost: {paths.paths[0].total_cost if hasattr(paths.paths[0], 'total_cost') else 'N/A'}")
    else:
        print("!!! 경로 탐색 실패 !!!")

if __name__ == "__main__":
    asyncio.run(test_design())
