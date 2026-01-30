import asyncio
import json
from app.core.wfs_client import WFSClient
from shapely.geometry import shape, Point
from app.utils.coordinate import calculate_distance

# 분석할 좌표 (전주 A 예상 위치)
POLE_A_X, POLE_A_Y = 14242617.97, 4432247.33
# 수용가 좌표 (데이터 조회 중심점)
CONSUMER_X, CONSUMER_Y = 14242588.22, 4432200.94

async def debug_data():
    client = WFSClient()
    print(f"=== WFS 데이터 정밀 분석 ===")
    
    try:
        data = await client.get_all_data(CONSUMER_X, CONSUMER_Y, bbox_size=400)
        
        poles = data.get('poles', [])
        lines = data.get('lines', [])
        transformers = data.get('transformers', [])
        
        # Combine all lines
        all_lines = lines + transformers
        
        print(f"조회 결과: 전주 {len(poles)}개, 전선 {len(lines)}개, 변압기/인입선 {len(transformers)}개")
        
        print(f"\n[특정 전선 분석: 3813307]")
        target_line = None
        for l in all_lines:
            gid = str(l['properties'].get('GID', l['properties'].get('FTR_IDN', '')))
            if gid == '3813307':
                target_line = l
                break
        
        if target_line:
            props = target_line['properties']
            print(f"  - 속성: {json.dumps(props, indent=2, ensure_ascii=False)}")
            text_annxn = str(props.get("TEXT_GIS_ANNXN", "")).upper()
            prwr_knd = str(props.get("PRWR_KND_CD", "")).upper()
            print(f"  - TEXT_GIS_ANNXN: {text_annxn}")
            print(f"  - PRWR_KND_CD: {prwr_knd}")
        else:
            print("  - 전선을 찾을 수 없습니다.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_data())
