
import asyncio
import json
from app.core.design_engine import DesignEngine
from app.models.response import DesignStatus

async def debug_coordinate(x, y):
    engine = DesignEngine()
    coord = f"{x},{y}"
    
    print(f"--- [테스트 시작] 좌표: {coord} ---")
    
    # 1. 단상 테스트
    print("\n[1. 단상(Single Phase) 설계 분석]")
    result_1 = await engine.run(coord, "1")
    if result_1.status == DesignStatus.SUCCESS:
        for route in result_1.routes[:3]:
            print(f"Rank {route.rank}: 전주 {route.start_pole_id}, 거리 {route.total_distance:.1f}m, "
                  f"신설전주 {route.new_poles_count}개, Index {route.cost_index}")
    else:
        print(f"단상 설계 실패: {result_1.message}")

    # 2. 3상 테스트
    print("\n[2. 3상(Three Phase) 설계 분석]")
    result_3 = await engine.run(coord, "3")
    if result_3.status == DesignStatus.SUCCESS:
        for route in result_3.routes[:3]:
            print(f"Rank {route.rank}: 전주 {route.start_pole_id}, 거리 {route.total_distance:.1f}m, "
                  f"신설전주 {route.new_poles_count}개, Index {route.cost_index}")
    else:
        print(f"3상 설계 실패: {result_3.message}")

if __name__ == "__main__":
    asyncio.run(debug_coordinate(14242388.49, 4436545.51))
