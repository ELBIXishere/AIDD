import pytest
from shapely.geometry import Point, LineString
from app.core.preprocessor import Pole, Line

def test_pole_model_extensions():
    """Pole 모델 확장 필드 테스트"""
    # 1. 전압값 기반 고압 판정
    pole_hv = Pole(
        id="P1",
        geometry=Point(0, 0),
        coord=(0, 0),
        voltage=22900
    )
    assert pole_hv.is_high_voltage is True
    
    # 2. 전압값 기반 저압 판정
    pole_lv = Pole(
        id="P2",
        geometry=Point(10, 10),
        coord=(10, 10),
        voltage=220
    )
    assert pole_lv.is_high_voltage is False
    
    # 3. 기존 로직(pole_type) fallback 테스트
    pole_legacy_hv = Pole(
        id="P3",
        geometry=Point(20, 20),
        coord=(20, 20),
        pole_type="H",
        voltage=None
    )
    assert pole_legacy_hv.is_high_voltage is True

def test_line_model_extensions():
    """Line 모델 확장 필드 테스트"""
    geom = LineString([(0, 0), (10, 10)])
    
    # 1. 신규 필드 저장 테스트
    line = Line(
        id="L1",
        geometry=geom,
        coords=[(0, 0), (10, 10)],
        wire_spec="ACSR_160",
        voltage=22900
    )
    assert line.wire_spec == "ACSR_160"
    assert line.voltage == 22900
    assert line.is_high_voltage is True
    
    # 2. 전압값 없는 경우 기존 타입 기반 판정
    line_legacy = Line(
        id="L2",
        geometry=geom,
        coords=[(0, 0), (10, 10)],
        line_type="HV",
        voltage=None
    )
    assert line_legacy.is_high_voltage is True

if __name__ == "__main__":
    # 간단한 실행 확인
    try:
        test_pole_model_extensions()
        test_line_model_extensions()
        print("✅ 모델 테스트 성공")
    except AssertionError as e:
        print(f"❌ 모델 테스트 실패: {e}")
