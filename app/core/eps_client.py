"""
ELBIX AIDD EPS (Electric Power System) 서버 클라이언트
- 고압전주 추적 API (connHvPoleTrace.do)
- 네트워크 추적 API (networkTrace.do)
- 계통 중복 검증
"""

import aiohttp
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class TraceResult:
    """추적 결과"""
    success: bool                        # 성공 여부
    pole_id: str = ""                    # 전주 ID
    connected_poles: List[str] = None    # 연결된 전주 목록
    feeder_id: str = ""                  # 피더(급전선) ID
    transformer_id: str = ""             # 변압기 ID
    raw_response: Dict[str, Any] = None  # 원본 응답
    error_message: str = ""
    
    def __post_init__(self):
        if self.connected_poles is None:
            self.connected_poles = []
        if self.raw_response is None:
            self.raw_response = {}


@dataclass
class DuplicateCheckResult:
    """중복 검증 결과"""
    has_duplicate: bool                  # 중복 여부
    duplicate_poles: List[str] = None    # 중복된 전주 목록
    message: str = ""
    
    def __post_init__(self):
        if self.duplicate_poles is None:
            self.duplicate_poles = []


class EPSClient:
    """
    EPS 서버 클라이언트
    
    계통 추적 및 중복 검증을 위한 API 호출
    """
    
    def __init__(self, eps_url: str = None, timeout: float = None):
        """
        Args:
            eps_url: EPS 서버 URL (기본: settings.EPS_BASE_URL)
            timeout: HTTP 타임아웃 (초)
        """
        self.eps_url = eps_url or settings.EPS_BASE_URL
        self.timeout = timeout or settings.HTTP_TIMEOUT
        
        # API 엔드포인트
        self.hv_pole_trace_url = f"{self.eps_url}{settings.EPS_HV_POLE_TRACE}"
        self.network_trace_url = f"{self.eps_url}{settings.EPS_NETWORK_TRACE}"
        
        logger.info(f"EPS 클라이언트 초기화: {self.eps_url}")
    
    async def trace_hv_pole(self, pole_id: str) -> TraceResult:
        """
        고압전주 계통 추적
        
        connHvPoleTrace.do API를 호출하여 전주의 계통 정보를 조회
        
        Args:
            pole_id: 전주 ID
        
        Returns:
            추적 결과
        """
        try:
            params = {
                "poleId": pole_id
            }
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    self.hv_pole_trace_url,
                    params=params
                ) as response:
                    response.raise_for_status()
                    
                    # 응답 파싱
                    text = await response.text()
                    
                    if text.strip().startswith('{'):
                        data = json.loads(text)
                    else:
                        # JSON이 아닌 경우
                        return TraceResult(
                            success=False,
                            pole_id=pole_id,
                            error_message=f"잘못된 응답 형식: {text[:100]}"
                        )
                    
                    # 결과 파싱
                    return TraceResult(
                        success=True,
                        pole_id=pole_id,
                        connected_poles=data.get("connectedPoles", []),
                        feeder_id=data.get("feederId", ""),
                        transformer_id=data.get("transformerId", ""),
                        raw_response=data
                    )
                    
        except aiohttp.ClientError as e:
            logger.error(f"EPS 고압전주 추적 HTTP 오류: {e}")
            return TraceResult(
                success=False,
                pole_id=pole_id,
                error_message=f"HTTP 오류: {str(e)}"
            )
        except Exception as e:
            logger.error(f"EPS 고압전주 추적 오류: {e}")
            return TraceResult(
                success=False,
                pole_id=pole_id,
                error_message=str(e)
            )
    
    async def trace_network(
        self,
        start_pole_id: str,
        end_pole_id: str = None
    ) -> TraceResult:
        """
        네트워크 추적
        
        networkTrace.do API를 호출하여 네트워크 경로 정보를 조회
        
        Args:
            start_pole_id: 시작 전주 ID
            end_pole_id: 끝 전주 ID (선택)
        
        Returns:
            추적 결과
        """
        try:
            params = {
                "startPoleId": start_pole_id
            }
            if end_pole_id:
                params["endPoleId"] = end_pole_id
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    self.network_trace_url,
                    params=params
                ) as response:
                    response.raise_for_status()
                    
                    text = await response.text()
                    
                    if text.strip().startswith('{'):
                        data = json.loads(text)
                    else:
                        return TraceResult(
                            success=False,
                            pole_id=start_pole_id,
                            error_message=f"잘못된 응답 형식: {text[:100]}"
                        )
                    
                    return TraceResult(
                        success=True,
                        pole_id=start_pole_id,
                        connected_poles=data.get("path", []),
                        feeder_id=data.get("feederId", ""),
                        raw_response=data
                    )
                    
        except aiohttp.ClientError as e:
            logger.error(f"EPS 네트워크 추적 HTTP 오류: {e}")
            return TraceResult(
                success=False,
                pole_id=start_pole_id,
                error_message=f"HTTP 오류: {str(e)}"
            )
        except Exception as e:
            logger.error(f"EPS 네트워크 추적 오류: {e}")
            return TraceResult(
                success=False,
                pole_id=start_pole_id,
                error_message=str(e)
            )
    
    async def check_network_duplicate(
        self,
        pole_ids: List[str]
    ) -> DuplicateCheckResult:
        """
        선택된 계통의 중복 여부 확인
        
        여러 전주가 동일한 피더/변압기에 연결되어 있는지 확인
        
        Args:
            pole_ids: 검사할 전주 ID 목록
        
        Returns:
            중복 검증 결과
        """
        if len(pole_ids) < 2:
            return DuplicateCheckResult(
                has_duplicate=False,
                message="검사할 전주가 2개 미만"
            )
        
        try:
            # 각 전주의 계통 정보 조회
            feeder_map: Dict[str, List[str]] = {}  # 피더ID → 전주ID 목록
            
            for pole_id in pole_ids:
                trace_result = await self.trace_hv_pole(pole_id)
                
                if trace_result.success and trace_result.feeder_id:
                    feeder_id = trace_result.feeder_id
                    if feeder_id not in feeder_map:
                        feeder_map[feeder_id] = []
                    feeder_map[feeder_id].append(pole_id)
            
            # 동일 피더에 2개 이상 전주가 있으면 중복
            duplicate_poles = []
            for feeder_id, poles in feeder_map.items():
                if len(poles) >= 2:
                    duplicate_poles.extend(poles)
                    logger.warning(
                        f"계통 중복 발견: 피더 {feeder_id}에 {poles} 연결"
                    )
            
            has_duplicate = len(duplicate_poles) > 0
            
            return DuplicateCheckResult(
                has_duplicate=has_duplicate,
                duplicate_poles=duplicate_poles,
                message=f"중복 전주: {duplicate_poles}" if has_duplicate else "중복 없음"
            )
            
        except Exception as e:
            logger.error(f"계통 중복 검사 오류: {e}")
            return DuplicateCheckResult(
                has_duplicate=False,
                message=f"검사 오류: {str(e)}"
            )
    
    async def verify_route_validity(
        self,
        start_pole_id: str,
        phase_code: str
    ) -> Dict[str, Any]:
        """
        경로 유효성 검증
        
        선택된 전주가 요청된 상(Phase)에 적합한지 확인
        
        Args:
            start_pole_id: 시작 기설전주 ID
            phase_code: 요청 상 코드 ("1": 단상, "3": 3상)
        
        Returns:
            검증 결과
        """
        try:
            # 전주 계통 추적
            trace_result = await self.trace_hv_pole(start_pole_id)
            
            if not trace_result.success:
                return {
                    "is_valid": False,
                    "reason": f"계통 추적 실패: {trace_result.error_message}"
                }
            
            # 응답에서 상 정보 확인 (API 응답 구조에 따라 조정 필요)
            raw = trace_result.raw_response
            pole_phase = raw.get("phaseCode", raw.get("phaseCd", ""))
            
            # 3상 요청인데 단상 전주인 경우 부적합
            if phase_code == "3" and pole_phase == "1":
                return {
                    "is_valid": False,
                    "reason": "3상 요청에 단상 전주 선택됨"
                }
            
            return {
                "is_valid": True,
                "pole_phase": pole_phase,
                "feeder_id": trace_result.feeder_id,
                "transformer_id": trace_result.transformer_id
            }
            
        except Exception as e:
            logger.error(f"경로 유효성 검증 오류: {e}")
            return {
                "is_valid": False,
                "reason": str(e)
            }
    
    async def health_check(self) -> bool:
        """
        EPS 서버 상태 확인
        
        Returns:
            서버 정상이면 True
        """
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.eps_url) as response:
                    return response.status < 500
        except Exception as e:
            logger.warning(f"EPS 서버 상태 확인 실패: {e}")
            return False
