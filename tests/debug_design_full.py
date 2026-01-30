import asyncio
import logging
from app.core.design_engine import DesignEngine
from app.config import settings

# 로깅 설정
logging.basicConfig(level=logging.INFO)

async def test_design_full():
    print("--- 설계 엔진 통합 테스트 시작 ---")
    
    # 충주 지역 테스트 좌표
    coord = "14242500,4432200"
    phase = "1"
    
    engine = DesignEngine()
    
    print(f"\n[설계 요청] 좌표: {coord}, 상: {phase}")
    
    try:
        result = await engine.run(coord=coord, phase_code=phase)
        
        print("\n[설계 결과]")
        print(f"Status: {result.status}")
        print(f"Error Message: {result.error_message}")
        print(f"Routes Found: {len(result.routes)}")
        
        for i, route in enumerate(result.routes):
            print(f"  Route {i+1}: Cost={route.total_cost}, Poles={route.new_poles_count}, Valid={route.remark or 'OK'}")
            
    except Exception as e:
        print(f"!!! 예외 발생 !!!: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_design_full())
