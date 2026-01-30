import asyncio
import json
from app.core.wfs_client import WFSClient
from app.config import settings

async def inspect_lines():
    client = WFSClient()
    # 충주 지역 중심부 bbox
    bbox = (14241000, 4431000, 14244000, 4433000)
    
    print(f"--- WFS 데이터 추출 시작 (레이어: {settings.LAYER_LINE}) ---")
    
    try:
        features = await client.get_facilities_by_bbox(bbox[0], bbox[1], bbox[2], bbox[3], max_features=300)
        lines = features.get('lines', [])
        
        if not lines:
            print("데이터를 찾을 수 없습니다. BBox를 조정하거나 서버 상태를 확인하세요.")
            return

        # 1. 통계 분석
        kinds = {}
        voltages = {}
        phases = {}
        
        print(f"\n[추출 결과 요약: {len(lines)}개 샘플]")
        print("-" * 60)
        
        for line in lines:
            props = line.get('properties', {})
            k = props.get('PRWR_KND_CD', '비어있음')
            v = props.get('VOLT_VAL', '비어있음')
            p = props.get('PHAR_CLCD', '비어있음')
            
            kinds[k] = kinds.get(k, 0) + 1
            voltages[v] = voltages.get(v, 0) + 1
            phases[p] = phases.get(p, 0) + 1

        print("전선 종류(PRWR_KND_CD) 분포:")
        for k, count in sorted(kinds.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {k: <10}: {count}개")
            
        print("\n전압(VOLT_VAL) 분포:")
        for v, count in sorted(voltages.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {str(v) + 'V': <10}: {count}개")

        # 2. 실제 행 데이터 (대표 샘플)
        print("\n[실제 데이터 행 상세 샘플]")
        print(f"{'GID':<8} | {'종류(KND)':<10} | {'전압(VOLT)':<10} | {'상(PHASE)':<10} | {'ID'}")
        print("-" * 75)
        # 각 종류별로 하나씩은 보여주기 위해 정렬
        seen_kinds = set()
        count = 0
        for line in lines:
            props = line.get('properties', {})
            kind = props.get('PRWR_KND_CD', '')
            if kind not in seen_kinds or count < 15:
                gid = str(props.get('GID', ''))
                volt = str(props.get('VOLT_VAL', ''))
                phase = str(props.get('PHAR_CLCD', ''))
                fid = str(line.get('id', ''))
                print(f"{gid:<8} | {kind:<10} | {volt:<10} | {phase:<10} | {fid}")
                seen_kinds.add(kind)
                count += 1
            if count >= 25: break

    except Exception as e:
        import traceback
        print(f"오류 발생: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(inspect_lines())