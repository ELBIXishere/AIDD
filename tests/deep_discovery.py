
import asyncio
import json
from app.core.wfs_client import WFSClient
from app.config import settings

async def deep_database_discovery():
    client = WFSClient()
    # 충주 지역 중심부 넉넉한 영역
    bbox = (14241000, 4431000, 14244000, 4433000)
    
    results = {}
    layers = {
        "Pole (전주)": settings.LAYER_POLE,
        "Line (전선)": settings.LAYER_LINE,
        "Transformer/Drop (변압기/인입선)": settings.LAYER_TRANSFORMER
    }

    print("="*80)
    print("ELBIX AIDD 근본 데이터 구조 전수 조사 보고서")
    print("="*80)

    for label, layer_name in layers.items():
        print(f"\n▶ [{label}] 분석 중... ({layer_name})")
        try:
            # 레이어별로 샘플 500개씩 추출하여 통계 분석
            features = await client.get_facilities_by_bbox(bbox[0], bbox[1], bbox[2], bbox[3], max_features=500)
            
            # WFSClient의 응답 키는 내부적으로 'poles', 'lines', 'transformers'로 고정됨
            key_map = {"Pole (전주)": "poles", "Line (전선)": "lines", "Transformer/Drop (변압기/인입선)": "transformers"}
            data_list = features.get(key_map[label], [])
            
            if not data_list:
                print("   - 데이터 없음")
                continue

            print(f"   - 총 {len(data_list)}개 샘플 확보")
            
            # 1. 모든 필드 목록 추출
            all_fields = set()
            for item in data_list:
                all_fields.update(item.get('properties', {}).keys())
            
            # 2. 필드별 유효 데이터(Non-null) 비율 및 샘플 값 확인
            field_stats = {}
            for field in all_fields:
                values = [str(item.get('properties', {}).get(field, '')).strip() for item in data_list]
                valid_values = [v for v in values if v and v != 'None' and v != '0']
                if valid_values:
                    # 빈도가 높은 값 상위 3개
                    from collections import Counter
                    top_3 = Counter(valid_values).most_common(3)
                    field_stats[field] = {
                        "fill_rate": len(valid_values) / len(data_list) * 100,
                        "samples": [f"{v}({c}개)" for v, c in top_3]
                    }

            # 3. 중요 필드 리포트
            print(f"   - 발견된 필드 수: {len(all_fields)}개")
            print(f"   - [주요 필드 통계 (값이 있는 상위 필드)]")
            # 채워진 비율이 높은 순으로 정렬
            sorted_fields = sorted(field_stats.items(), key=lambda x: x[1]['fill_rate'], reverse=True)
            for field, stat in sorted_fields[:15]:
                print(f"     * {field:<20}: {stat['fill_rate']:>5.1f}% 채워짐 | 샘플: {', '.join(stat['samples'])} ")

        except Exception as e:
            print(f"   - 오류 발생: {e}")

    print("\n" + "="*80)
    print("조사 완료")

if __name__ == "__main__":
    asyncio.run(deep_database_discovery())
