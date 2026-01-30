import asyncio
from app.core.wfs_client import WFSClient
from shapely.geometry import shape, LineString, Point
import json

# Target coordinates
CONSUMER_COORD = (14242588.22, 4432200.94)
# Path coordinates from previous successful run (when validator was off)
PATH_COORDS = [
    [14242588.22, 4432200.94],
    [14242612.276172547, 4432200.501275098],
    [14242612.4378513, 4432209.36644778],
    [14242612.8445422, 4432221.47456553],
    [14242613.9424882, 4432232.68441661],
    [14242615.1738501, 4432239.71374143],
    [14242616.1447257, 4432246.92108838],
    [14242619.3348895, 4432247.24577636]
]

async def analyze_intersection():
    client = WFSClient()
    print("=== 경로 vs 기존 전선 기하학적 관계 분석 ===")
    
    try:
        data = await client.get_all_data(CONSUMER_COORD[0], CONSUMER_COORD[1], bbox_size=200)
        lines = data.get('lines', []) + data.get('transformers', [])
        
        path_geom = LineString(PATH_COORDS)
        
        print(f"총 {len(lines)}개의 전선과 비교합니다.")
        
        found_issue = False
        for l in lines:
            l_geom = shape(l['geometry'])
            l_id = l['properties'].get('GID') or l['properties'].get('FTR_IDN')
            
            if path_geom.intersects(l_geom):
                intersection = path_geom.intersection(l_geom)
                
                # Check if it's just a touch at endpoints
                is_touch = path_geom.touches(l_geom)
                is_cross = path_geom.crosses(l_geom)
                is_overlap = path_geom.overlaps(l_geom) # This is False for lines usually, use relate
                
                # Precise relation (DE-9IM)
                rel = path_geom.relate(l_geom)
                
                print(f"\n[전선 {l_id}]")
                print(f"  - 관계 매트릭스: {rel}")
                print(f"  - 단순 접촉(Touches): {is_touch}")
                print(f"  - 교차(Crosses): {is_cross}")
                print(f"  - 교차점 형태: {intersection.geom_type}")
                
                if intersection.geom_type == 'LineString':
                    print(f"  - [발견] 두 선이 평행하게 겹침 (길이: {intersection.length:.2f}m)")
                    found_issue = True
                elif is_cross:
                    print(f"  - [발견] X자 교차 발생")
                    found_issue = True
                elif not is_touch:
                    # Intersects but not touches and not crosses? 
                    # Usually means points of one line are interior to the other.
                    print(f"  - [발견] 부분적 중첩 또는 T자 교차")
                    found_issue = True
                else:
                    print(f"  - 정상 연결 (끝점 접촉)")

        if not found_issue:
            print("\n기하학적 교차 문제가 발견되지 않았습니다. (알고리즘의 과잉 판정 가능성)")

    except Exception as e:
        print(f"오류: {e}")

if __name__ == "__main__":
    asyncio.run(analyze_intersection())
