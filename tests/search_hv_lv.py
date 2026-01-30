
import asyncio
from app.core.wfs_client import WFSClient

async def search_literal_hv_lv():
    client = WFSClient()
    # 검색 범위를 대폭 확대 (충주 전역 수준)
    bboxes = [
        (14240000, 4430000, 14250000, 4440000),
        (14230000, 4420000, 14260000, 4450000)
    ]
    
    print(f"--- 'HV' 또는 'LV' 문자열이 직접 입력된 데이터 검색 중... ---")
    
    found_count = 0
    try:
        for bbox in bboxes:
            features = await client.get_facilities_by_bbox(bbox[0], bbox[1], bbox[2], bbox[3], max_features=5000)
            lines = features.get('lines', [])
            
            for line in lines:
                props = line.get('properties', {})
                kind = str(props.get('PRWR_KND_CD', '')).upper()
                
                if kind in ['HV', 'LV', '고압', '저압', 'H', 'L']:
                    print(f"발견! [GID: {props.get('GID')}] 종류: {kind} | 상: {props.get('PHAR_CLCD')} | 전압: {props.get('VOLT_VAL')}")
                    found_count += 1
                    if found_count >= 10: break
            if found_count >= 10: break

        if found_count == 0:
            print("\n[결과] 이 지역 데이터베이스에는 'HV', 'LV'라는 글자 자체가 입력된 행이 아예 없습니다.")
            print("대신 모든 전선이 EC(절연), EW(가공지선), TW(인입선) 등의 '재질/용도 코드'로 관리되고 있습니다.")

    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    asyncio.run(search_literal_hv_lv())
