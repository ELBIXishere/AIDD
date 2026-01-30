
import asyncio
from app.core.wfs_client import WFSClient
from app.config import settings

async def exhaustive_voltage_search():
    client = WFSClient()
    # 충주 지역 중심부 + 주변부까지 넓게 설정
    bbox = (14240000, 4430000, 14250000, 4440000)
    
    layers = {
        "전주 (001)": settings.LAYER_POLE,
        "전선 (002)": settings.LAYER_LINE,
        "변압기/인입선 (003)": settings.LAYER_TRANSFORMER
    }

    print("="*80)
    print("전압(Voltage) 데이터 존재 여부 정밀 추적 보고서")
    print("="*80)

    for label, layer_name in layers.items():
        print(f"\n▶ [{label}] 레이어 스캔 중...")
        try:
            # 레이어당 2000개씩 대량 추출
            features = await client.get_facilities_by_bbox(bbox[0], bbox[1], bbox[2], bbox[3], max_features=2000)
            
            key_map = {"전주 (001)": "poles", "전선 (002)": "lines", "변압기/인입선 (003)": "transformers"}
            data_list = features.get(key_map[label], [])
            
            if not data_list:
                print("   - 데이터 없음")
                continue

            found_volt_fields = {}
            voltage_keywords = ['VOLT', 'VAL', 'NOM', 'POT', 'VLT', '전압']
            
            for item in data_list:
                props = item.get('properties', {})
                for field, value in props.items():
                    # 1. 필드명에 전압 관련 키워드가 있는 경우
                    if any(kw in field.upper() for kw in voltage_keywords):
                        if value and str(value).strip() not in ['None', '0', '']:
                            found_volt_fields[field] = found_volt_fields.get(field, 0) + 1
                    
                    # 2. 필드명과 상관없이 값이 전형적인 전압값(22900, 380, 220 등)인 경우
                    val_str = str(value).strip()
                    if val_str in ['22900', '380', '220', '13200', '6600']:
                        print(f"      !!! 값 발견: 필드[{field}] = {val_str} (GID: {props.get('GID')})")

            if found_volt_fields:
                print("   - [전압 의심 필드 통계]")
                for field, count in found_volt_fields.items():
                    print(f"     * {field:<20}: {count}개 행에 값이 있음")
            else:
                print("   - 전압 관련 필드에 유효한 데이터가 발견되지 않았습니다.")

        except Exception as e:
            print(f"   - 오류 발생: {e}")

    print("\n" + "="*80)
    print("추적 완료")

if __name__ == "__main__":
    asyncio.run(exhaustive_voltage_search())
