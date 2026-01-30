import asyncio
import logging
import json
from app.core.design_engine import DesignEngine
from app.config import settings

# 로깅 설정
logging.basicConfig(level=logging.INFO)

async def test_real_coordinate():
    """실제 좌표를 사용한 설계 엔진 테스트"""
    
    # 테스트 좌표
    coord = "14242588.22, 4432200.94"
    phase_code = "1" # 단상
    load_kw = 5.0
    
    print(f"=== 설계 테스트 시작: {coord} ===")
    
    engine = DesignEngine()
    result = await engine.run(coord, phase_code, load_kw)
    
    print(f"\n=== 결과 요약 ===")
    print(f"상태: {result.status}")
    
    if result.status == "success":
        print(f"경로 개수: {len(result.routes)}")
        if result.routes:
            best_route = result.routes[0]
            print(f"최적 경로 총 비용: {best_route.total_cost:,}원")
            print(f"총 거리: {best_route.total_distance:.1f}m")
            print(f"신설 전주: {best_route.new_poles_count}개")
            print(f"시작 전주 ID: {best_route.start_pole_id}")
            print(f"기설 전압 타입: {best_route.source_voltage_type}")
            print(f"기설 상 타입: {best_route.source_phase_type}")
            
            vd = best_route.voltage_drop
            print(f"\n[전압 강하 정보]")
            print(f"  - 전압 강하: {vd.voltage_drop_percent:.2f}% ({vd.voltage_drop_v:.1f}V)")
            print(f"  - 허용 여부: {vd.is_acceptable}")
            print(f"  - 메시지: {vd.message}")
            
            # JSON 형태로 일부 출력 (프론트엔드 응답 구조 확인용)
            # print("\n[API 응답 미리보기]")
            # print(json.dumps(best_route.dict(), indent=2, ensure_ascii=False)[:500] + "...")
    else:
        print(f"오류 메시지: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(test_real_coordinate())
