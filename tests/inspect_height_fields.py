import asyncio
import json
from app.core.wfs_client import WFSClient

# Coordinates for analysis
X, Y = 14242588.22, 4432200.94

async def inspect_fields():
    client = WFSClient()
    print(f"=== WFS 데이터 속성 필드 전수 조사 ===")
    
    try:
        data = await client.get_all_data(X, Y, bbox_size=400)
        
        layers = {
            "Poles (전주)": data.get('poles', []),
            "Lines (전선)": data.get('lines', []),
            "Transformers (변압기/인입선)": data.get('transformers', [])
        }
        
        for layer_name, features in layers.items():
            print(f"\n--- {layer_name} ---")
            if not features:
                print("데이터 없음")
                continue
            
            # 모든 고유 키 수집
            all_keys = set()
            for f in features:
                all_keys.update(f['properties'].keys())
            
            print(f"발견된 필드 수: {len(all_keys)}")
            
            # 높이/규격 관련 의심 필드 필터링
            keywords = ['HGHT', 'ALT', 'ELEV', 'SPEC', 'LEN', 'DIST', 'Z', 'LEVEL', 'VER', 'OFFSET', 'ANNXN']
            suspected_keys = sorted([k for k in all_keys if any(kw in k.upper() for kw in keywords)])
            
            print("높이/규격 관련 의심 필드 목록:")
            for k in suspected_keys:
                # 샘플 값 3개 추출
                samples = []
                for f in features:
                    val = f['properties'].get(k)
                    if val is not None and val != "":
                        samples.append(str(val))
                    if len(samples) >= 3:
                        break
                print(f"  - {k.ljust(20)} : {', '.join(samples) if samples else 'N/A'}")

            # 전체 필드 리스트 (참고용)
            # print("전체 필드 리스트:", sorted(list(all_keys)))

    except Exception as e:
        print(f"조회 중 오류 발생: {e}")

if __name__ == "__main__":
    asyncio.run(inspect_fields())
