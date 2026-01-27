"""
디버깅용 테스트 스크립트
"""
import asyncio
import logging

# 로깅 설정
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')

from app.core.wfs_client import WFSClient
from app.core.preprocessor import DataPreprocessor
from app.core.target_selector import TargetSelector
from app.core.graph_builder import RoadGraphBuilder
from app.core.pathfinder import Pathfinder
from app.config import settings


async def main():
    # 테스트 좌표
    consumer_x = 14241940.817790061
    consumer_y = 4437601.6755945515
    phase_code = "1"  # 단상
    
    print(f"\n=== 테스트 시작 ===")
    print(f"수용가 좌표: ({consumer_x}, {consumer_y})")
    print(f"상 코드: {phase_code}")
    
    # 1. WFS 데이터 수집
    print(f"\n=== Phase 1: WFS 데이터 수집 ===")
    wfs_client = WFSClient()
    raw_data = await wfs_client.get_all_data(consumer_x, consumer_y, 400)
    
    print(f"전주: {len(raw_data['poles'])}개")
    print(f"전선: {len(raw_data['lines'])}개")
    print(f"도로: {len(raw_data['roads'])}개")
    print(f"건물: {len(raw_data['buildings'])}개")
    
    # 전주 샘플 확인
    if raw_data['poles']:
        print(f"\n전주 샘플: {raw_data['poles'][0]}")
    
    # 도로 샘플 확인
    if raw_data['roads']:
        print(f"\n도로 샘플: {raw_data['roads'][0]}")
    
    # 2. 데이터 전처리
    print(f"\n=== Phase 2: 데이터 전처리 ===")
    preprocessor = DataPreprocessor()
    processed_data = preprocessor.process(raw_data)
    
    print(f"전처리 후 전주: {len(processed_data.poles)}개")
    print(f"전처리 후 전선: {len(processed_data.lines)}개")
    print(f"전처리 후 도로: {len(processed_data.roads)}개")
    print(f"전처리 후 건물: {len(processed_data.buildings)}개")
    
    # 3. 후보 전주 선별
    print(f"\n=== Phase 3: 후보 전주 선별 ===")
    selector = TargetSelector(processed_data)
    selection_result = selector.select((consumer_x, consumer_y), phase_code)
    
    print(f"후보 전주: {len(selection_result.targets)}개")
    print(f"메시지: {selection_result.message}")
    
    if selection_result.targets:
        for i, target in enumerate(selection_result.targets[:5]):
            print(f"  {i+1}. {target.id} - 거리: {target.distance_to_consumer:.1f}m, Fast Track: {target.is_fast_track}")
    
    if not selection_result.targets:
        print("후보 전주가 없어서 테스트 종료")
        return
    
    # 4. 도로 네트워크 그래프 구축
    print(f"\n=== Phase 4: 도로 네트워크 그래프 ===")
    if not processed_data.roads:
        print("도로 데이터가 없습니다!")
        return
    
    graph_builder = RoadGraphBuilder(processed_data)
    road_graph = graph_builder.build(
        (consumer_x, consumer_y),
        selection_result.targets
    )
    
    print(f"그래프 노드: {road_graph.graph.number_of_nodes()}개")
    print(f"그래프 엣지: {road_graph.graph.number_of_edges()}개")
    print(f"연결된 전주: {len(road_graph.pole_node_ids)}개")
    
    # 5. 경로 탐색
    print(f"\n=== Phase 5: 경로 탐색 ===")
    pathfinder = Pathfinder(road_graph)
    pathfinding_result = pathfinder.find_paths(selection_result.targets)
    
    print(f"탐색된 경로: {len(pathfinding_result.paths)}개")
    
    if pathfinding_result.paths:
        for i, path in enumerate(pathfinding_result.paths[:3]):
            print(f"  {i+1}. {path.target_pole_id} - 거리: {path.total_distance:.1f}m, 도달: {path.is_reachable}")
    
    print(f"\n=== 테스트 완료 ===")


if __name__ == "__main__":
    asyncio.run(main())
