import asyncio
import logging
from app.core.design_engine import DesignEngine
from app.config import settings
from app.utils.coordinate import calculate_distance

# 로깅 설정
logging.basicConfig(level=logging.INFO)

async def debug_connectivity():
    print("--- 전주-도로 연결성 정밀 분석 ---")
    
    # 입력 좌표
    consumer_coord = (14242588.22, 4432200.94)
    pole_a_coord = (14242646.05, 4432049.70) # 먼 전주 (A)
    pole_b_coord = (14242679.12, 4432246.63) # 가까운 전주 (B)
    
    engine = DesignEngine()
    
    # 1. 데이터 수집
    print("\n[1. 데이터 수집]")
    raw_data = await engine.wfs_client.get_all_data(consumer_coord[0], consumer_coord[1], settings.BBOX_SIZE)
    
    from app.core.preprocessor import DataPreprocessor
    preprocessor = DataPreprocessor()
    processed = preprocessor.process(raw_data)
    
    # 전주 찾기
    def find_pole(target_coord):
        best_p = None
        min_d = float('inf')
        for p in processed.poles:
            d = calculate_distance(target_coord[0], target_coord[1], p.coord[0], p.coord[1])
            if d < min_d:
                min_d = d
                best_p = p
        return best_p, min_d

    pole_a, dist_a = find_pole(pole_a_coord)
    pole_b, dist_b = find_pole(pole_b_coord)
    
    if pole_a: print(f"Pole A (Far) Found: {pole_a.id} (Distance to Target: {dist_a:.1f}m)")
    else: print("Pole A Not Found")
    
    if pole_b: print(f"Pole B (Near) Found: {pole_b.id} (Distance to Target: {dist_b:.1f}m)")
    else: print("Pole B Not Found")

    if not pole_a or not pole_b:
        return

    # 2. 도로 연결 테스트
    print("\n[2. 도로 연결성 테스트]")
    from app.core.graph_builder import RoadGraphBuilder
    from shapely.geometry import Point, LineString
    from shapely.ops import nearest_points
    
    builder = RoadGraphBuilder(processed)
    # 그래프 구축 (내부적으로 _connect_point_to_road 호출)
    # 우리는 로직을 직접 시뮬레이션해서 거리를 봅니다.
    
    def check_road_connection(pole, label):
        print(f"\n[{label} 연결 분석] ID: {pole.id}")
        pole_point = Point(pole.coord)
        min_dist = float('inf')
        nearest_road_id = None
        
        for road in processed.roads:
            if not road.geometry: continue
            # 도로와 전주 거리 계산
            dist = road.geometry.distance(pole_point)
            if dist < min_dist:
                min_dist = dist
                nearest_road_id = road.id
        
        print(f"  - 가장 가까운 도로 거리: {min_dist:.2f}m")
        limit = settings.ROAD_ACCESS_DISTANCE
        if min_dist > limit:
            print(f"  Result: 연결 실패 (거리 {min_dist:.2f}m > 제한 {limit}m)")
        else:
            print(f"  Result: 연결 성공 (제한 {limit}m 이내)")

    check_road_connection(pole_a, "Pole A (Far)")
    check_road_connection(pole_b, "Pole B (Near)")

if __name__ == "__main__":
    asyncio.run(debug_connectivity())
