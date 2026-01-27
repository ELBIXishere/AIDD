"""
ELBIX AIDD 성능 모니터링 유틸리티
- 함수 실행 시간 측정
- 메모리 사용량 추적
- 병목 지점 분석
"""

import time
import logging
import functools
import asyncio
from typing import Callable, Any, Dict, List, Optional
from dataclasses import dataclass, field
from contextlib import contextmanager
import threading

logger = logging.getLogger(__name__)


@dataclass
class ProfileResult:
    """프로파일링 결과"""
    function_name: str
    execution_time_ms: float
    call_count: int = 1
    avg_time_ms: float = 0.0
    min_time_ms: float = float('inf')
    max_time_ms: float = 0.0


class ProfileStats:
    """프로파일링 통계 수집기 (싱글톤)"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._stats: Dict[str, ProfileResult] = {}
                    cls._instance._enabled = True
        return cls._instance
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value
    
    def record(self, func_name: str, elapsed_ms: float):
        """실행 시간 기록"""
        if not self._enabled:
            return
        
        with self._lock:
            if func_name not in self._stats:
                self._stats[func_name] = ProfileResult(
                    function_name=func_name,
                    execution_time_ms=elapsed_ms,
                    call_count=1,
                    avg_time_ms=elapsed_ms,
                    min_time_ms=elapsed_ms,
                    max_time_ms=elapsed_ms
                )
            else:
                stat = self._stats[func_name]
                stat.call_count += 1
                stat.execution_time_ms += elapsed_ms
                stat.min_time_ms = min(stat.min_time_ms, elapsed_ms)
                stat.max_time_ms = max(stat.max_time_ms, elapsed_ms)
                stat.avg_time_ms = stat.execution_time_ms / stat.call_count
    
    def get_stats(self) -> Dict[str, ProfileResult]:
        """전체 통계 반환"""
        return dict(self._stats)
    
    def get_summary(self) -> str:
        """통계 요약 문자열 반환"""
        if not self._stats:
            return "No profiling data collected"
        
        lines = ["\n=== 성능 프로파일링 요약 ==="]
        
        # 총 실행 시간 순으로 정렬
        sorted_stats = sorted(
            self._stats.values(),
            key=lambda x: x.execution_time_ms,
            reverse=True
        )
        
        for stat in sorted_stats:
            lines.append(
                f"  {stat.function_name}: "
                f"총 {stat.execution_time_ms:.2f}ms, "
                f"호출 {stat.call_count}회, "
                f"평균 {stat.avg_time_ms:.2f}ms, "
                f"최소 {stat.min_time_ms:.2f}ms, "
                f"최대 {stat.max_time_ms:.2f}ms"
            )
        
        return "\n".join(lines)
    
    def clear(self):
        """통계 초기화"""
        with self._lock:
            self._stats.clear()
    
    def print_summary(self):
        """통계 요약 출력"""
        print(self.get_summary())


# 전역 프로파일러 인스턴스
_profiler = ProfileStats()


def profile(func: Callable) -> Callable:
    """
    동기 함수 프로파일링 데코레이터
    
    사용법:
        @profile
        def my_function():
            ...
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not _profiler.enabled:
            return func(*args, **kwargs)
        
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            _profiler.record(func.__qualname__, elapsed_ms)
            logger.debug(f"[Profile] {func.__qualname__}: {elapsed_ms:.2f}ms")
    
    return wrapper


def profile_async(func: Callable) -> Callable:
    """
    비동기 함수 프로파일링 데코레이터
    
    사용법:
        @profile_async
        async def my_async_function():
            ...
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        if not _profiler.enabled:
            return await func(*args, **kwargs)
        
        start = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            _profiler.record(func.__qualname__, elapsed_ms)
            logger.debug(f"[Profile] {func.__qualname__}: {elapsed_ms:.2f}ms")
    
    return wrapper


@contextmanager
def profile_block(name: str):
    """
    코드 블록 프로파일링 컨텍스트 매니저
    
    사용법:
        with profile_block("데이터 처리"):
            process_data()
    """
    if not _profiler.enabled:
        yield
        return
    
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        _profiler.record(name, elapsed_ms)
        logger.debug(f"[Profile] {name}: {elapsed_ms:.2f}ms")


class Timer:
    """
    간단한 타이머 클래스
    
    사용법:
        timer = Timer()
        # 작업 수행
        elapsed = timer.elapsed_ms()
    """
    
    def __init__(self):
        self.start_time = time.perf_counter()
    
    def reset(self):
        """타이머 리셋"""
        self.start_time = time.perf_counter()
    
    def elapsed_ms(self) -> float:
        """경과 시간 (밀리초)"""
        return (time.perf_counter() - self.start_time) * 1000
    
    def elapsed_sec(self) -> float:
        """경과 시간 (초)"""
        return time.perf_counter() - self.start_time


def get_profiler() -> ProfileStats:
    """프로파일러 인스턴스 반환"""
    return _profiler


def enable_profiling():
    """프로파일링 활성화"""
    _profiler.enabled = True


def disable_profiling():
    """프로파일링 비활성화"""
    _profiler.enabled = False


def clear_profiling_stats():
    """프로파일링 통계 초기화"""
    _profiler.clear()


def print_profiling_summary():
    """프로파일링 요약 출력"""
    _profiler.print_summary()


def get_profiling_summary() -> str:
    """프로파일링 요약 문자열 반환"""
    return _profiler.get_summary()


# 메모리 사용량 측정 (선택적)
try:
    import tracemalloc
    
    def start_memory_tracking():
        """메모리 추적 시작"""
        tracemalloc.start()
    
    def get_memory_usage() -> Dict[str, Any]:
        """현재 메모리 사용량 반환"""
        if not tracemalloc.is_tracing():
            return {"error": "Memory tracking not started"}
        
        current, peak = tracemalloc.get_traced_memory()
        return {
            "current_mb": current / 1024 / 1024,
            "peak_mb": peak / 1024 / 1024
        }
    
    def stop_memory_tracking():
        """메모리 추적 중지"""
        tracemalloc.stop()

except ImportError:
    def start_memory_tracking():
        logger.warning("tracemalloc not available")
    
    def get_memory_usage() -> Dict[str, Any]:
        return {"error": "tracemalloc not available"}
    
    def stop_memory_tracking():
        pass
