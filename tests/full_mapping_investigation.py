
import asyncio
import json
from app.core.wfs_client import WFSClient
from app.config import settings
from shapely.geometry import shape, Point

async def database_full_mapping():
    client = WFSClient()
    # 전주 A 주변을 포함한 넓은 영역 (충주 핵심부)
    bbox = (14241000, 4431000, 14244000, 4433000)
    
    print("="*80)
    print("시설물 계통 연관 관계 전수 조사 보고서")
    print("="*80)

    try:
        # 데이터 대량 수집 (각 레이어당 2000개)
        features = await client.get_all_data(bbox[0], bbox[1], settings.BBOX_SIZE * 2)
        
        raw_poles = features.get('poles', [])
        raw_lines = features.get('lines', [])
        raw_tr = features.get('transformers', []) # 인입선 포함
        
        print(f"수집된 데이터: 전주 {len(raw_poles)}개, 간선 {len(raw_lines)}개, 인입선 {len(raw_tr)}개")

        # 1. 모든 전선의 성격 분류 (HV/LV)
        line_map = {} # line_id -> type
        for l in raw_lines:
            props = l.get('properties', {})
            phase = str(props.get('PHAR_CLCD', ''))
            is_hv = len(phase) >= 3 or props.get('PRWR_KND_CD') in ['EC', 'EW']
            line_map[l.get('id')] = "HV" if is_hv else "LV"

        # 2. 전주별 연결된 전선 분석
        pole_connections = {} # pole_gid -> set(line_types)
        
        def link_pole(pole_gid, line_type):
            if not pole_gid: return
            gid = str(pole_gid)
            if gid not in pole_connections:
                pole_connections[gid] = set()
            pole_connections[gid].add(line_type)

        # 간선 연결 분석
        for l in raw_lines:
            props = l.get('properties', {})
            l_type = line_map.get(l.get('id'))
            link_pole(props.get('LWER_FAC_GID'), l_type)
            link_pole(props.get('UPPO_FAC_GID'), l_type)

        # 인입선 연결 분석
        for t in raw_tr:
            props = t.get('properties', {})
            # 인입선은 무조건 LV
            link_pole(props.get('LWER_FAC_GID'), "LV")
            link_pole(props.get('UPPO_FAC_GID'), "LV")

        # 3. 전주 타입 매핑 통계
        print("\n[전주별 실제 계통 연결 통계]")
        stats = {"HV_ONLY": 0, "LV_ONLY": 0, "MIXED": 0, "NONE": 0}
        
        for p in raw_poles:
            gid = str(p.get('properties', {}).get('GID', ''))
            conns = pole_connections.get(gid, set())
            
            if "HV" in conns and "LV" in conns: stats["MIXED"] += 1
            elif "HV" in conns: stats["HV_ONLY"] += 1
            elif "LV" in conns: stats["LV_ONLY"] += 1
            else: stats["NONE"] += 1

        print(f"  - 고압 전용 전주: {stats['HV_ONLY']}개")
        print(f"  - 저압 전용 전주: {stats['LV_ONLY']}개")
        print(f"  - 혼용 전주 (HV+LV): {stats['MIXED']}개")
        print(f"  - 연결 정보 없음: {stats['NONE']}개")

        # 4. 전주 A(3599730) 정밀 조사
        target_id = "3599730"
        print(f"\n[전주 {target_id} 정밀 분석]")
        conns = pole_connections.get(target_id, set())
        print(f"  - 실제 연결된 전선 타입: {list(conns)}")
        
        # 실제 연결된 전선 ID들 찾기
        connected_line_details = []
        for l in raw_lines + raw_tr:
            props = l.get('properties', {})
            if str(props.get('LWER_FAC_GID')) == target_id or str(props.get('UPPO_FAC_GID')) == target_id:
                connected_line_details.append({
                    "id": l.get('id'),
                    "kind": props.get('PRWR_KND_CD') or props.get('TEXT_GIS_ANNXN'),
                    "phase": props.get('PHAR_CLCD')
                })
        
        for detail in connected_line_details:
            print(f"    * 연결선: {detail['id']} | 종류: {detail['kind']} | 상: {detail['phase']}")

    except Exception as e:
        import traceback
        print(f"오류 발생: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(database_full_mapping())
