"""
ELBIX AIDD 설정 관리
- 서버 URL, 좌표계, 상수 정의
- 전주/전선 규격별 단가, 전압 강하 설정
"""

from pydantic_settings import BaseSettings
from typing import Optional, Dict


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # ===== 애플리케이션 기본 설정 =====
    APP_NAME: str = "ELBIX AIDD"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # ===== WFS 서버 URL =====
    # GIS WFS: 전주, 전선, 변압기
    GIS_WFS_URL: str = "http://192.168.0.71:8881/orange/wfs?GDX=AI_FAC.xml"
    
    # BASE WFS: 도로, 건물, 철도, 하천
    BASE_WFS_URL: str = "http://192.168.0.71:8881/orange/wfs?GDX=AI_BASE.xml"
    
    # VIEW WFS: 뷰 레이어
    VIEW_WFS_URL: str = "http://192.168.0.71:8881/orange/wfs?GDX=AI_FAC.xml"
    
    # ===== EPS 서버 URL =====
    EPS_BASE_URL: str = "http://192.168.0.71:8881/ai/"
    EPS_HV_POLE_TRACE: str = "connHvPoleTrace.do"  # 고압전주 추적
    EPS_NETWORK_TRACE: str = "networkTrace.do"     # 네트워크 추적
    
    # ===== VWorld API =====
    VWORLD_KEY: str = "F1849B6C-14D6-3F57-97F7-98BBFE66CFB"
    
    # ===== 좌표계 설정 =====
    # 입력 좌표계 (Web Mercator)
    INPUT_CRS: str = "EPSG:3857"
    # 처리 좌표계 (UTM Zone 52N - 한국)
    PROCESS_CRS: str = "EPSG:32652"
    # WGS84 (경위도)
    WGS84_CRS: str = "EPSG:4326"
    
    # ===== WFS 레이어명 =====
    # GIS 레이어 (AI_FAC.xml)
    LAYER_POLE: str = "AI_FAC_001.GIS_LOC"            # 전주
    LAYER_LINE: str = "AI_FAC_002.GIS_PTH"            # 전선 (경간)
    LAYER_TRANSFORMER: str = "AI_FAC_003.GIS_PTH"     # 변압기/인입선
    
    # GIS 지오메트리 필드
    GEOM_POLE: str = "GIS_LOC"
    GEOM_LINE: str = "GIS_PTH"
    
    # BASE 레이어 (AI_BASE.xml)
    # 주의: 실제 WFS 서버 데이터 기준 매핑
    LAYER_ROAD: str = "AI_BASE_002.GIS_PTH_VAL"       # 도로 (RD_NM 속성)
    LAYER_BUILDING: str = "AI_BASE_004.GIS_AREA_VAL"  # 건물 (GIS_BLD_CL_NM 속성)
    LAYER_RAILWAY: str = "AI_BASE_003.GIS_AREA_VAL"   # 철도
    LAYER_RIVER: str = "AI_BASE_001.GIS_AREA_VAL"     # 하천/기타 영역
    
    # BASE 지오메트리 필드
    GEOM_ROAD: str = "GIS_PTH_VAL"
    GEOM_BUILDING: str = "GIS_AREA_VAL"
    GEOM_RAILWAY: str = "GIS_AREA_VAL"     # 철도
    GEOM_RIVER: str = "GIS_AREA_VAL"       # 하천
    
    # GIS 변압기 지오메트리 필드
    GEOM_TRANSFORMER: str = "GIS_PTH"
    
    # ===== 설계 제약조건 상수 =====
    # 최대 거리 제한 (수용가 ~ 기설전주)
    MAX_DISTANCE_LIMIT: float = 400.0  # meters
    
    # BBox 크기 (수용가 중심 탐색 영역)
    BBOX_SIZE: float = 400.0  # meters (400m x 400m)
    
    # Fast Track 거리 (외선 불요 판단)
    FAST_TRACK_DISTANCE: float = 50.0  # meters
    
    # 전주 배치 간격
    POLE_INTERVAL: float = 40.0  # meters
    
    # 첫 전주 최대 거리 (수용가로부터)
    FIRST_POLE_MAX_DISTANCE: float = 30.0  # meters
    
    # 도로 접근성 거리 (전주/수용가가 도로에서 이 거리 이내)
    ROAD_ACCESS_DISTANCE: float = 100.0  # meters (도로에서 멀리 떨어진 수용가/전주 허용)
    
    # 끊긴 도로 연결 허용 거리 (Snapping)
    ROAD_SNAP_DISTANCE: float = 10.0  # meters
    
    # ===== 공사비 단가 (원) - 기본값 =====
    # 전주 표준 단가 (기본)
    COST_POLE: int = 500000  # 원/개
    
    # 전선 단가 (저압)
    COST_WIRE_LV: int = 5000  # 원/m
    
    # 전선 단가 (고압)
    COST_WIRE_HV: int = 8000  # 원/m
    
    # 기본 노무비
    COST_LABOR_BASE: int = 200000  # 원
    
    # 도로 횡단 추가 비용
    COST_ROAD_CROSSING: int = 100000  # 원/회
    
    # ===== 전주 규격별 단가 (원) =====
    # 콘크리트 전주
    COST_POLE_C10: int = 350000    # C종 10m 콘크리트 전주
    COST_POLE_C12: int = 450000    # C종 12m 콘크리트 전주
    COST_POLE_C14: int = 550000    # C종 14m 콘크리트 전주
    # 강관 전주
    COST_POLE_STEEL_10: int = 800000   # 강관 10m 전주
    COST_POLE_STEEL_12: int = 950000   # 강관 12m 전주
    
    # ===== 전선 규격별 단가 (원/m) =====
    # ACSR (알루미늄 도체 강심 알루미늄 연선)
    COST_WIRE_ACSR_58: int = 6500    # ACSR 58mm²
    COST_WIRE_ACSR_95: int = 8500    # ACSR 95mm²
    COST_WIRE_ACSR_160: int = 12000  # ACSR 160mm²
    # OW (옥외용 비닐절연전선)
    COST_WIRE_OW_22: int = 5500      # OW 22mm²
    COST_WIRE_OW_38: int = 7000      # OW 38mm²
    
    # ===== 부자재 단가 (원) =====
    COST_INSULATOR_LP: int = 45000       # LP애자 (현수애자)
    COST_INSULATOR_PIN: int = 25000      # 핀애자
    COST_INSULATOR_LINE_POST: int = 35000  # 라인포스트애자
    COST_ARM_TIE: int = 35000            # 완금 (Arm Tie)
    COST_CLAMP: int = 15000              # 전선 클램프
    COST_CONNECTOR: int = 8000           # 전선 접속자재
    
    # ===== 인건비 단가 (원) =====
    COST_LABOR_POLE_INSTALL: int = 250000    # 전주 설치 인건비/본
    COST_LABOR_WIRE_STRETCH: int = 15000     # 전선 가선 인건비/m
    COST_LABOR_INSULATOR: int = 20000        # 애자 설치 인건비/개
    
    # ===== 경비율 =====
    OVERHEAD_RATE: float = 0.15          # 경비율 15%
    PROFIT_RATE: float = 0.10            # 이윤율 10%
    
    # ===== 전압 강하 설정 =====
    # 허용 전압 강하율 (%)
    VOLTAGE_DROP_LIMIT_LV: float = 6.0   # 저압: 6% 이내
    VOLTAGE_DROP_LIMIT_HV: float = 3.0   # 고압: 3% 이내
    
    # 공칭 전압 (V)
    NOMINAL_VOLTAGE_LV: int = 220        # 저압 단상
    NOMINAL_VOLTAGE_LV_3P: int = 380     # 저압 3상
    NOMINAL_VOLTAGE_HV: int = 22900      # 고압 22.9kV
    
    # 전선 저항값 (Ω/km) - 20°C 기준
    WIRE_RESISTANCE_ACSR_58: float = 0.595   # ACSR 58mm²
    WIRE_RESISTANCE_ACSR_95: float = 0.363   # ACSR 95mm²
    WIRE_RESISTANCE_ACSR_160: float = 0.215  # ACSR 160mm²
    WIRE_RESISTANCE_OW_22: float = 0.827     # OW 22mm²
    WIRE_RESISTANCE_OW_38: float = 0.480     # OW 38mm²
    
    # 전선 리액턴스값 (Ω/km)
    WIRE_REACTANCE_ACSR_58: float = 0.380
    WIRE_REACTANCE_ACSR_95: float = 0.355
    WIRE_REACTANCE_ACSR_160: float = 0.330
    WIRE_REACTANCE_OW_22: float = 0.400
    WIRE_REACTANCE_OW_38: float = 0.380
    
    # ===== 변압기 설정 =====
    # 변압기 용량별 단가 (kVA → 원)
    COST_TRANSFORMER_10: int = 2500000   # 10kVA
    COST_TRANSFORMER_20: int = 3000000   # 20kVA
    COST_TRANSFORMER_30: int = 3500000   # 30kVA
    COST_TRANSFORMER_50: int = 4500000   # 50kVA
    COST_TRANSFORMER_100: int = 6500000  # 100kVA
    COST_TRANSFORMER_200: int = 9500000  # 200kVA
    
    # 변압기 과부하 경고 기준 (이용률)
    TRANSFORMER_OVERLOAD_WARNING: float = 0.75  # 75% 초과 시 경고
    TRANSFORMER_OVERLOAD_LIMIT: float = 1.0     # 100% 초과 불가
    
    # 역률 기본값
    DEFAULT_POWER_FACTOR: float = 0.9
    
    # ===== 경로 탐색 가중치 =====
    # 거리 가중치 (기본)
    WEIGHT_DISTANCE: float = 1.0
    
    # 전주 신설 가중치 (40m마다 비용 증가 반영)
    WEIGHT_POLE_COST: float = 12500.0  # COST_POLE / POLE_INTERVAL
    
    # ===== 상(Phase) 코드 =====
    PHASE_SINGLE: str = "1"   # 단상
    PHASE_THREE: str = "3"    # 3상
    
    # ===== 경로 평가 점수 가중치 (PRD 4.2) =====
    SCORE_WEIGHT_POLE: int = 10000       # 전주당 점수
    SCORE_WEIGHT_DISTANCE: float = 1.0   # m당 점수
    SCORE_WEIGHT_TURN: int = 50          # 굴절당 점수
    
    # ===== HTTP 클라이언트 설정 =====
    HTTP_TIMEOUT: float = 30.0  # seconds
    
    # ===== CORS 설정 =====
    # 허용할 오리진 목록 (쉼표로 구분)
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001"
    
    # 세션 보안 설정
    SESSION_SECRET_KEY: str = "elbix-aidd-secret-key-2026"  # 운영 환경에서는 반드시 변경!
    SESSION_HTTPS_ONLY: bool = False  # HTTPS 사용 시 True로 변경
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # .env의 추가 변수(domain, vite_api_url 등) 무시


# 전역 설정 인스턴스
settings = Settings()
