
import asyncio
import json
from app.core.wfs_client import WFSClient
from app.config import settings

async def inspect_pole_and_tr():
    client = WFSClient()
    bbox = (14241000, 4431000, 14244000, 4433000)
    
    print("--- 전주(Pole) 및 변압기(TR) 데이터 정밀 분석 시작 ---")
    
    try:
        # 1. 전주 데이터 분석
        print(f"\n[1. 전주 레이어 분석: {settings.LAYER_POLE}]")
        pole_data = await client.get_facilities_by_bbox(bbox[0], bbox[1], bbox[2], bbox[3], max_features=50)
        poles = pole_data.get('poles', [])
        
        if poles:
            sample_props = poles[0].get('properties', {})
            print("사용 가능한 모든 필드(Fields):", list(sample_props.keys()))
            print("-" * 50)
            print(f"{ 'GID':<10} | { 'FORM_CD':<10} | { 'SPEC_CD':<10} | { 'PHASE':<10} | {'ID'}")
            for p in poles[:10]:
                props = p.get('properties', {})
                print(f"{str(props.get('GID', '')): <10} | {str(props.get('POLE_FORM_CD', '')): <10} | {str(props.get('POLE_SPEC_CD', '')): <10} | {str(props.get('PHAR_CLCD', '')): <10} | {props.get('POLE_ID', '')}")
        else:
            print("전주 데이터를 찾을 수 없습니다.")

        # 2. 변압기 데이터 분석
        print(f"\n[2. 변압기 레이어 분석: {settings.LAYER_TRANSFORMER}]")
        tr_data = await client.get_facilities_by_bbox(bbox[0], bbox[1], bbox[2], bbox[3], max_features=50)
        transformers = tr_data.get('transformers', [])
        
        if transformers:
            sample_props = transformers[0].get('properties', {})
            print("사용 가능한 모든 필드(Fields):", list(sample_props.keys()))
            print("-" * 50)
            print(f"{ 'GID':<10} | { 'CAP_KVA':<10} | { 'VOLT':<10} | { 'TYPE':<10}")
            for tr in transformers[:10]:
                props = tr.get('properties', {})
                print(f"{str(props.get('GID', '')): <10} | {str(props.get('CAP_KVA', '')): <10} | {str(props.get('VOLT_VAL', '')): <10} | {str(props.get('TR_TYPE', '')): <10}")
        else:
            print("변압기 데이터를 찾을 수 없습니다.")

    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    asyncio.run(inspect_pole_and_tr())
