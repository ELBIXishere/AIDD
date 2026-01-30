import asyncio
import logging
from app.core.design_engine import DesignEngine
from app.config import settings
from app.utils.coordinate import calculate_distance

# 로깅 설정
logging.basicConfig(level=logging.INFO)

async def debug_scenario():
    print("--- 알고리즘 의사결정 추적 (시나리오 분석) ---")
    
    # 입력 좌표
    consumer_coord = (14242588.22, 4432200.94)
    pole_a_coord = (14242646.05, 4432049.70) # 단상 선택 (Far)
    pole_b_coord = (14242679.12, 4432246.63) # 3상 선택 (Near)
    
    print(f"수용가: {consumer_coord}")
    print(f"Pole A (단상Pick): {pole_a_coord}")
    print(f"Pole B (3상Pick): {pole_b_coord}")
    
    engine = DesignEngine()
    
    # 1. 데이터 수집
    print("\n[1. 데이터 수집 & 전처리]")
    raw_data = await engine.wfs_client.get_all_data(consumer_coord[0], consumer_coord[1], settings.BBOX_SIZE)
    
    from app.core.preprocessor import DataPreprocessor
    preprocessor = DataPreprocessor()
    processed = preprocessor.process(raw_data)
    
    # 전주 찾기
    def find_pole(target_coord):
        best_p = None
        min_d = float('inf')
        for p in processed.poles:
            d = calculate_distance(target_coord[0], target_coord[1], p.coord[0], p.coord[1])
            if d < min_d:
                min_d = d
                best_p = p
        return best_p, min_d

    # 원본 데이터에서 Pole B 확인
    print(f"\n[Raw Data 분석] Pole B 근처 검색")
    raw_min_d = float('inf')
    raw_best_p = None
    for p_data in raw_data['poles']:
        # Geometry 파싱
        from shapely.geometry import shape, Point
        geom = shape(p_data['geometry'])
        d = calculate_distance(pole_b_coord[0], pole_b_coord[1], geom.x, geom.y)
        if d < raw_min_d:
            raw_min_d = d
            raw_best_p = p_data
            
    if raw_best_p:
        props = raw_best_p.get('properties', {})
        print(f"  - 원본 최단 전주: ID={props.get('GID')}, 거리={raw_min_d:.1f}m")
        print(f"  - 상태: {props.get('FAC_STAT_CD')}, 형태: {props.get('POLE_FORM_CD')}, 제거여부: {props.get('REMOVE_YN')}")
    else:
        print("  - 원본 데이터에서도 찾을 수 없음")

    pole_a, dist_a = find_pole(pole_a_coord)
    pole_b, dist_b = find_pole(pole_b_coord)
    
    if not pole_a:
        print(f"!!! Pole A를 찾을 수 없음 (오차 {dist_a}m) !!!")
        # return # 계속 진행
    else:
        print(f"Pole A 매칭 성공: {pole_a.id} (거리 {dist_a:.1f}m)")

    if not pole_b:
        print(f"!!! Pole B를 찾을 수 없음 (오차 {dist_b}m) !!!")
        # return # 계속 진행
    else:
        print(f"Pole B 매칭 성공: {pole_b.id} (거리 {dist_b:.1f}m)")
        
    if not pole_a or not pole_b:
        print("분석 대상 전주가 없어 종료합니다.")
        return
        
    print(f"\n[Pole A 분석] ID: {pole_a.id}")
    print(f"  - 좌표: {pole_a.coord}")
    print(f"  - 거리: {calculate_distance(consumer_coord[0], consumer_coord[1], pole_a.coord[0], pole_a.coord[1]):.1f}m")
    print(f"  - 속성: Type={pole_a.pole_type}, Phase={pole_a.phase_code}, HV={pole_a.is_high_voltage}, 3P={pole_a.is_three_phase}")
    
    print(f"\n[Pole B 분석] ID: {pole_b.id}")
    print(f"  - 좌표: {pole_b.coord}")
    print(f"  - 거리: {calculate_distance(consumer_coord[0], consumer_coord[1], pole_b.coord[0], pole_b.coord[1]):.1f}m")
    print(f"  - 속성: Type={pole_b.pole_type}, Phase={pole_b.phase_code}, HV={pole_b.is_high_voltage}, 3P={pole_b.is_three_phase}")

    # TargetSelector 분석
    from app.core.target_selector import TargetSelector
    selector = TargetSelector(processed)
    
    # 연결 상태 분석
    conn_a = selector._analyze_pole_connections(pole_a.id)
    conn_b = selector._analyze_pole_connections(pole_b.id)
    print(f"\n[연결 상태]")
    print(f"  - Pole A: {conn_a}")
    print(f"  - Pole B: {conn_b}")

    # 점수 계산 시뮬레이션
    def calculate_score(target_pole, phase_req):
        dist = calculate_distance(consumer_coord[0], consumer_coord[1], target_pole.coord[0], target_pole.coord[1])
        score = dist
        conn = selector._analyze_pole_connections(target_pole.id)
        
        bonus = 0
        if phase_req == "1" and conn['has_lv']:
            bonus = 50.0
            score -= 50.0
        elif phase_req == "3" and conn['has_hv_3phase']:
            bonus = 100.0
            score -= 100.0
            
        return score, bonus

    print("\n[Case 1: 단상(1상) 요청]")
    score_a_1, bonus_a_1 = calculate_score(pole_a, "1")
    score_b_1, bonus_b_1 = calculate_score(pole_b, "1")
    print(f"  - Pole A: 거리 {int(score_a_1 + bonus_a_1)}m - 보너스 {bonus_a_1} = 최종점수 {int(score_a_1)}")
    print(f"  - Pole B: 거리 {int(score_b_1 + bonus_b_1)}m - 보너스 {bonus_b_1} = 최종점수 {int(score_b_1)}")
    
    if score_a_1 < score_b_1:
        print("  => 결과: Pole A 우선 (점수가 더 낮음)")
    else:
        print("  => 결과: Pole B 우선 (점수가 더 낮음)")

    print("\n[Case 2: 3상 요청]")
    # 3상 가능 여부 체크
    valid_a_3 = pole_a.id in [p.id for p in selector._phase_matching("3")]
    valid_b_3 = pole_b.id in [p.id for p in selector._phase_matching("3")]
    
    print(f"  - Pole A: 3상 연결 가능? {valid_a_3}")
    print(f"  - Pole B: 3상 연결 가능? {valid_b_3}")
    
    if valid_a_3:
        score_a_3, bonus_a_3 = calculate_score(pole_a, "3")
        print(f"    -> 점수: {int(score_a_3)}")
    if valid_b_3:
        score_b_3, bonus_b_3 = calculate_score(pole_b, "3")
        print(f"    -> 점수: {int(score_b_3)}")

if __name__ == "__main__":
    asyncio.run(debug_scenario())
