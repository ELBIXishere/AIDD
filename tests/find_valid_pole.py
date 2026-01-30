import asyncio
import aiohttp
import logging
from app.core.wfs_client import WFSClient
from app.config import settings

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def find_valid_pole():
    """WFS에서 전주를 가져와 EPS 서버에 조회 테스트"""
    
    # 테스트 좌표
    coord_x, coord_y = 14242588.22, 4432200.94
    
    logger.info("1. WFS 데이터 수집 중...")
    wfs_client = WFSClient()
    raw_data = await wfs_client.get_all_data(coord_x, coord_y, bbox_size=400)
    poles = raw_data.get('poles', [])
    
    logger.info(f"WFS에서 전주 {len(poles)}개 발견")
    
    valid_pole_id = None
    
    async with aiohttp.ClientSession() as session:
        for i, pole_data in enumerate(poles):
            props = pole_data.get('properties', {})
            pole_id = str(props.get("GID") or props.get("POLE_ID") or "")
            
            if not pole_id:
                continue
                
            url = f"{settings.EPS_BASE_URL}connHvPoleTrace.do?poleId={pole_id}"
            try:
                async with session.get(url, timeout=2.0) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ 유효한 전주 발견! ID: {pole_id}, 응답: {data}")
                        valid_pole_id = pole_id
                        break
                    else:
                        logger.warning(f"❌ 실패 ({i+1}/{len(poles)}): ID={pole_id}, Status={response.status}")
            except Exception as e:
                logger.error(f"⚠️ 에러 ({i+1}/{len(poles)}): ID={pole_id}, {e}")
                
    if valid_pole_id:
        print(f"\n[결과] 테스트 가능한 전주 ID: {valid_pole_id}")
    else:
        print("\n[결과] 이 지역에서 유효한 EPS 전주를 찾을 수 없습니다.")

if __name__ == "__main__":
    asyncio.run(find_valid_pole())
