
import asyncio
import json
from app.core.wfs_client import WFSClient
from app.config import settings

async def find_volt_data():
    client = WFSClient()
    # 더 넓은 영역 탐색
    bbox = (14240000, 4430000, 14250000, 4440000)
    
    print(f"--- 전압 정보(VOLT_VAL)가 있는 데이터 찾는 중... ---")
    
    try:
        # 최대 2000개까지 훑으며 전압 값이 있는 것만 골라냅니다.
        features = await client.get_facilities_by_bbox(bbox[0], bbox[1], bbox[2], bbox[3], max_features=2000)
        lines = features.get('lines', [])
        
        volt_lines = []
        for line in lines:
            props = line.get('properties', {})
            volt = props.get('VOLT_VAL')
            # 전압 값이 존재하고, 빈 문자열이나 0이 아닌 경우
            if volt and str(volt).strip() and str(volt) != '0':
                volt_lines.append(line)
            if len(volt_lines) >= 10:
                break

        if not volt_lines:
            print("\n[결과] 검색 범위 내에 전압 정보가 입력된 행이 없습니다.")
            print("이 데이터베이스는 전압(VOLT_VAL) 필드를 주로 비워두고 종류(KND) 코드로 관리하는 것으로 보입니다.")
            return

        print(f"\n[전압 정보가 있는 행 10개 발견]")
        print("-" * 85)
        print(f"{ 'GID':<10} | { '종류(KND)':<10} | { '전압(VOLT)':<10} | { '상(PHASE)':<10} | {'ID'}")
        print("-" * 85)
        
        for line in volt_lines:
            props = line.get('properties', {})
            print(f"{str(props.get('GID', '')): <10} | {str(props.get('PRWR_KND_CD', '')): <10} | {str(props.get('VOLT_VAL', '')): <10} | {str(props.get('PHAR_CLCD', '')): <10} | {line.get('id', '')}")

    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    asyncio.run(find_volt_data())
