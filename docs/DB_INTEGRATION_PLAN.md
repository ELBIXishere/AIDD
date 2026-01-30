# 데이터베이스 기반 전압/공사비 고도화 계획 (DB Integration Plan)

**목표:** `ref_code.py` 및 WFS 데이터 구조를 분석하여, 하드코딩된 가정이 아닌 **실제 DB 필드 값(전압, 상, 전선 규격)**을 `VoltageCalculator` 및 `CostCalculator`에 주입하여 계산 정확도를 극대화함.

---

## 📅 전체 로드맵

- **Phase 1: 데이터 모델링 및 매핑 정의 (Foundation)** [완료]
  - 실제 DB 필드와 애플리케이션 내부 변수 간의 매핑 테이블 확정
  - Pydantic 모델(`models/`) 및 내부 데이터 클래스 업데이트
- **Phase 2: 전처리 로직 및 파이프라인 연결 (Implementation)** [완료]
  - `wfs_client.py`: 누락된 필드 요청 확인
  - `preprocessor.py`: 원시 코드(CD) 파싱 및 정규화 로직 구현
  - `design_engine.py`: 계산기에 실제 값 전달
- **Phase 3: 테스트 및 검증 (Verification)** [완료]
  - 단위 테스트 업데이트 및 통합 테스트 수행
  - 기존 하드코딩 방식 대비 개선 효과 검증

---

## 🚀 Phase 1: 데이터 모델링 및 매핑 정의

**핵심 목표:** 데이터를 담을 그릇(Model)을 실제 DB 구조에 맞게 확장하고, 변수명을 통일합니다.

### 📋 To-Do List
1. [x] **DB-Code 필드 매핑 테이블 작성**
   - `ref_code.py`와 `docs/전압_관련_정보_조회_보고서.md`를 기반으로 매핑 정의.
   - 예: `PHAR_CLCD` (ABC) → `phase_type` ("3")
   - 예: `PRWR_SPEC_CD` (160) → `wire_spec` ("ACSR_160")
2. [x] **데이터 모델 업데이트 (`app/models/`)**
   - `Pole` 및 `Line` 관련 Pydantic 모델에 `voltage_val`, `phase_spec`, `wire_spec_code` 등 필드 추가.
3. [x] **설정 파일 업데이트 (`app/config.py`)**
   - DB에서 넘어오는 코드값(예: "OW", "ACSR")과 내부 Enum 매핑 설정 추가.

### 🧪 Test Plan
- `test_models.py` (신규 생성): 모델이 새로운 DB 필드를 제대로 수용하는지 테스트.
- Pydantic 유효성 검사 테스트.

### ✅ Completion Checklist
- [x] DB 필드와 내부 변수 간의 매핑 문서가 코드 주석이나 문서로 존재함.
- [x] `app/models/` 내의 클래스들이 실제 DB의 모든 관련 필드를 포함하고 있음.

---

## ⚙️ Phase 2: 전처리 로직 및 파이프라인 연결

**핵심 목표:** WFS에서 데이터를 가져와 파싱(Parsing)하고, 계산 엔진까지 데이터가 흐르도록 파이프라인을 연결합니다.

### 📋 To-Do List
1. [x] **WFS 클라이언트 점검 (`app/core/wfs_client.py`)**
   - WFS 요청 시 `VOLT_VAL`, `PHAR_CLCD`, `PRWR_SPEC_CD` 등의 필드가 `PropertyName`에 포함되어 있는지 확인 및 수정.
2. [x] **전처리 로직 대수술 (`app/core/preprocessor.py`)**
   - **상(Phase) 파싱:** `PHAR_CLCD` 값("ABC", "A" 등)을 분석하여 "3" 또는 "1"로 변환하는 함수 구현.
   - **규격 파싱:** `PRWR_SPEC_CD`와 `PRWR_KND_CD`를 조합하여 `WireType` Enum으로 변환.
   - **전압 파싱:** `VOLT_VAL`이 유효하면 사용, 없으면 `POLE_FORM_CD` 등을 통한 기존 추론 로직을 Fallback으로 사용.
3. [x] **그래프 빌더 업데이트 (`app/core/graph_builder.py`)**
   - 노드(Node)와 엣지(Edge) 속성에 파싱된 전압/상/규격 정보 저장.
4. [x] **설계 엔진 연동 (`app/core/design_engine.py`)**
   - `VoltageCalculator.calculate()` 호출 시 하드코딩된 값이 아닌, 그래프 엣지에서 가져온 실제 속성값 주입.

### 🧪 Test Plan
- `tests/debug_real_data.py` 실행: 실제 WFS 데이터가 `preprocessor`를 통과했을 때 올바른 `phase`, `voltage` 값을 내는지 로그 확인.
- `test_preprocessor.py` (단위 테스트): 다양한 코드값("ABC", "CBA", "A", "R")에 대한 파싱 로직 검증.

### ✅ Completion Checklist
- [x] 전처리 과정에서 DB의 Raw Data가 내부 Enum/표준값으로 정확히 변환됨.
- [x] `design_engine.py`가 실제 데이터를 계산기에 전달하고 있음.

---

## 🔍 Phase 3: 테스트 및 검증

**핵심 목표:** 변경된 로직이 실제 데이터 환경에서 버그 없이 작동하며, 공학적으로 타당한 결과를 내는지 확인합니다.

### 📋 To-Do List
1. [x] **통합 테스트 수행 (`tests/test_integration.py`)**
   - 전체 파이프라인 실행 시 에러 발생 여부 확인.
2. [x] **전압 강하 리포트 비교**
   - 기존 방식(하드코딩) vs 신규 방식(DB 기반) 결과 비교.
   - 극단적인 케이스(예: 장거리 단상 선로)에서 전압 강하가 제대로 계산되어 경고가 뜨는지 확인.
3. [x] **공사비 산출 검증**
   - 전선 규격이 자동 변경됨에 따라 공사비 내역서의 자재비가 변동되는지 확인.
4. [x] **코드 정리 및 문서화**
   - 주석 정리, 불필요한 디버그 코드 제거.
   - `API 문서` 업데이트 (입출력 필드 변경 시).

### 🧪 Test Plan
- `tests/voltage_report.py` 재실행: DB 필드 조회율(NULL이 아닌 비율) 재확인.
- 시나리오 테스트: 특정 구간을 강제로 "단상, 얇은 전선"으로 설정했을 때 전압 강하로 인해 경로가 변경되거나 전선이 굵어지는지 시뮬레이션.

### ✅ Completion Checklist
- [x] 통합 테스트(CI) 통과.
- [x] 전압 강하 계산 결과가 물리 법칙 및 DB 데이터와 일치함.
- [x] 사용자(클라이언트) 입장에서 API 응답이 정상적임.