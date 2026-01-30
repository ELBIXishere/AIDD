import pytest
from app.core.preprocessor import DataPreprocessor, Line
from shapely.geometry import Point, LineString

def test_ref_code_alignment():
    """ref_code 정렬 확인 테스트: HV/LV 분리 및 변압기 처리"""
    preprocessor = DataPreprocessor()
    
    # Mock Raw Data matching new WFSClient structure
    raw_data = {
        "poles": [],
        "lines_hv": [
            {
                "geometry": {"type": "LineString", "coordinates": [[0, 0], [10, 10]]},
                "properties": {
                    "GID": "HV1",
                    "PHAR_CLCD": "ABC", # 3상
                    "VOLT_VAL": "22900"
                }
            }
        ],
        "lines_lv": [
            {
                "geometry": {"type": "LineString", "coordinates": [[10, 10], [20, 20]]},
                "properties": {
                    "GID": "LV1",
                    "PRWR_KND_CD": "OW", # 저압 본선
                    "PHAR_CLCD": "A",    # 단상
                }
            },
            {
                "geometry": {"type": "LineString", "coordinates": [[20, 20], [25, 25]]},
                "properties": {
                    "GID": "LV2",
                    "PRWR_KND_CD": "DV", # 인입선
                    "PHAR_CLCD": "A",
                }
            }
        ],
        "transformers": [
            {
                "geometry": {"type": "Point", "coordinates": [5, 5]},
                "properties": {
                    "GID": "TR1",
                    "CAP_KVA": "50",
                    "PHAR_CLCD": "ABC"
                }
            }
        ],
        "roads": [],
        "buildings": []
    }
    
    processed = preprocessor.process(raw_data)
    
    # 1. Line Check
    assert len(processed.lines) == 3
    
    hv_line = next(l for l in processed.lines if l.id == "HV1")
    assert hv_line.line_type == "HV"
    assert hv_line.is_obstacle == True
    assert hv_line.phase_code == "3"
    
    lv_main = next(l for l in processed.lines if l.id == "LV1")
    assert lv_main.line_type == "LV"
    assert lv_main.is_obstacle == True # 본선은 장애물
    assert lv_main.phase_code == "1"
    
    lv_drop = next(l for l in processed.lines if l.id == "LV2")
    assert lv_drop.line_type == "LV"
    assert lv_drop.is_obstacle == False # 인입선은 장애물 아님
    
    # 2. Transformer Check
    assert len(processed.transformers) == 1
    tr = processed.transformers[0]
    assert tr.id == "TR1"
    assert tr.capacity_kva == 50.0
    assert tr.phase_code == "3"
    
    print("✅ ref_code 정렬 테스트 성공")

if __name__ == "__main__":
    test_ref_code_alignment()
