import pytest
from app.core.preprocessor import DataPreprocessor, Pole
from app.core.voltage_calculator import VoltageCalculator, WireType
from app.config import settings

def test_preprocessor_parsing():
    """WFS 데이터 파싱 및 필드 매핑 테스트"""
    preprocessor = DataPreprocessor()
    
    raw_poles = [{
        "geometry": {"type": "Point", "coordinates": [0, 0]},
        "properties": {
            "GID": "P1",
            "VOLT_VAL": "440",  # 특수 전압 (440V)
            "POLE_KND_CD": "C"
        }
    }]
    
    raw_lines = [{
        "geometry": {"type": "LineString", "coordinates": [[0, 0], [10, 10]]},
        "properties": {
            "GID": "L1",
            "PHAR_CLCD": "ABC",       # 3상
            "PRWR_SPEC_CD": "160",    # ACSR 160
            "PRWR_KND_CD": "ACSR",    # 고압
            "VOLT_VAL": "22900"
        }
    }]
    
    raw_data = {
        "poles": raw_poles, 
        "lines": raw_lines,
        "roads": [], 
        "buildings": [],
        "transformers": []
    }
    
    processed = preprocessor.process(raw_data)
    
    # Pole 검증
    pole = processed.poles[0]
    assert pole.voltage == 440.0
    
    # Line 검증
    line = processed.lines[0]
    assert line.phase_code == "3"
    assert line.wire_spec == "ACSR_160"
    assert line.voltage == 22900.0
    assert line.is_high_voltage is True
    
    print("✅ Preprocessor 파싱 테스트 성공")

def test_voltage_calculator_override():
    """전압값 오버라이드 계산 테스트"""
    calc = VoltageCalculator()
    
    distance = 100.0
    load_kw = 10.0
    
    # Case 1: 기본값 (220V 단상)
    res_default = calc.calculate(distance, load_kw, phase_type="1")
    
    # Case 2: 오버라이드 (110V 단상) - 전압이 낮으므로 전압 강하(%)는 커져야 함
    # V_drop_percent = (V_drop / V_nominal) * 100
    # V_drop ∝ I ∝ 1/V_nominal
    # 따라서 V_drop_percent ∝ 1/(V_nominal^2)
    res_override = calc.calculate(distance, load_kw, phase_type="1", voltage_override=110.0)
    
    print(f"Default(220V) Drop: {res_default.voltage_drop_percent}%")
    print(f"Override(110V) Drop: {res_override.voltage_drop_percent}%")
    
    assert res_override.voltage_drop_percent > res_default.voltage_drop_percent
    assert res_override.voltage_drop_percent > (res_default.voltage_drop_percent * 3) # 약 4배 차이 예상
    
    print("✅ VoltageCalculator 오버라이드 테스트 성공")

if __name__ == "__main__":
    test_preprocessor_parsing()
    test_voltage_calculator_override()
