# ELBIX AIDD 개발 보고서

## AI 기반 배전 설계 자동화 시스템

**버전**: 1.0.0  
**작성일**: 2026-01-26

---

## 1. 프로젝트 개요

### 1.1 목적
ELBIX AIDD(AI Distribution Design)는 신규 수용가(전력 사용자)의 전력 공급을 위한 배전 설계를 자동화하는 시스템이다. 기존 수작업 설계 프로세스를 AI 기반으로 자동화하여 설계 시간을 단축하고 최적 경로를 산출한다.

### 1.2 핵심 기능
- **자동 경로 탐색**: 수용가 위치에서 기설 전주까지 최적 경로 산출
- **신설 전주 배치**: 40m 간격으로 신설 전주 자동 배치
- **공사비 산출**: 자재비, 노무비, 경비 포함 상세 견적
- **제약조건 검증**: 전선 교차, 건물 간섭, 전압 강하 등 자동 검증

---

## 2. 시스템 아키텍처

### 2.1 처리 파이프라인

```
[수용가 좌표 입력]
        ↓
[Phase 1] WFS 데이터 수집 (전주, 전선, 도로, 건물)
        ↓
[Phase 2] 데이터 전처리 (정제, 필터링, 공간 연결)
        ↓
[Phase 3] 후보 전주 선별 (Phase Matching, 거리 필터)
        ↓
[Phase 4] 도로 네트워크 그래프 구축 (NetworkX)
        ↓
[Phase 5] 경로 탐색 (A* 알고리즘)
        ↓
[Phase 5.5] 전선 교차 검증 (FR-05)
        ↓
[Phase 6] 신설 전주 배치 (40m 간격)
        ↓
[Phase 7] 공사비 계산 (상세 견적)
        ↓
[Phase 8] EPS 서버 검증 (계통 중복 체크)
        ↓
[Phase 9] 전압 강하 계산 및 결과 출력
```

### 2.2 핵심 모듈 구조

| 모듈 | 파일 | 역할 |
|------|------|------|
| 설계 엔진 | `design_engine.py` | 전체 파이프라인 통합 |
| WFS 클라이언트 | `wfs_client.py` | GIS 데이터 수집 |
| 데이터 전처리기 | `preprocessor.py` | 데이터 정제/변환 |
| 후보 선별기 | `target_selector.py` | Phase Matching |
| 그래프 빌더 | `graph_builder.py` | 도로 네트워크 구축 |
| **경로 탐색기** | `pathfinder.py` | **A* 알고리즘** |
| 전선 검증기 | `line_validator.py` | 교차 검증 |
| 전주 배치기 | `pole_allocator.py` | 신설 전주 배치 |
| 비용 계산기 | `cost_calculator.py` | 공사비 산출 |

---

## 3. 경로 탐색 로직 (핵심)

### 3.1 도로 네트워크 그래프 구축

배전 설계에서 전선은 도로를 따라 설치되어야 한다. 이를 위해 도로 중심선을 기반으로 가중치 그래프를 구축한다.

```python
# graph_builder.py - 그래프 구축
class RoadGraphBuilder:
    def build(self, consumer_coord, target_poles) -> RoadGraph:
        # Step 1: 도로 중심선을 그래프 노드/엣지로 변환
        self._build_road_graph()
        
        # Step 2: 끊긴 도로 연결 (Snapping, 10m 이내)
        self._snap_disconnected_roads()
        
        # Step 3: 수용가 노드를 도로에 연결
        consumer_node_id = self._add_consumer_node(consumer_coord)
        
        # Step 4: 후보 전주 노드를 도로에 연결
        pole_node_ids = self._add_pole_nodes(target_poles)
        
        return RoadGraph(graph, nodes, consumer_node_id, pole_node_ids)
```

**가중치 계산 공식**:
```python
def _calculate_weight(self, distance: float) -> float:
    # 기본 거리 가중치
    weight = distance * WEIGHT_DISTANCE
    
    # 전주 비용 가중치 (40m당 전주 1개 비용 반영)
    weight += (distance / POLE_INTERVAL) * COST_POLE / 100
    
    return weight
```

### 3.2 A* 알고리즘 기반 경로 탐색

Dijkstra 대신 A* 알고리즘을 사용하여 탐색 효율을 높였다.

```python
# pathfinder.py - A* 경로 탐색
class Pathfinder:
    def __init__(self, road_graph: RoadGraph, use_astar: bool = True):
        self.road_graph = road_graph
        self.graph = road_graph.graph
        self.use_astar = use_astar
        
        # 휴리스틱 캐시 (중복 계산 방지)
        self._heuristic_cache: Dict[Tuple[str, str], float] = {}
    
    def _euclidean_heuristic(self, node_id: str, target_id: str) -> float:
        """A* 휴리스틱 함수 (유클리드 거리)"""
        cache_key = (node_id, target_id)
        if cache_key in self._heuristic_cache:
            return self._heuristic_cache[cache_key]
        
        n1 = self.nodes[node_id].coord
        n2 = self.nodes[target_id].coord
        h = math.sqrt((n2[0] - n1[0])**2 + (n2[1] - n1[1])**2)
        
        self._heuristic_cache[cache_key] = h
        return h
    
    def _astar_path(self, source, target, target_pole, max_distance=400):
        """A* 알고리즘으로 최단 가중치 경로 탐색"""
        
        def heuristic(n1, n2):
            return self._euclidean_heuristic(n1, n2)
        
        # NetworkX의 astar_path 사용
        path_nodes = nx.astar_path(
            self.graph,
            source,
            target,
            heuristic=heuristic,
            weight='weight'
        )
        
        # 경로 좌표 및 거리 추출
        path_coords = []
        total_distance = 0.0
        total_weight = 0.0
        
        for i, node_id in enumerate(path_nodes):
            coord = self.nodes[node_id].coord
            path_coords.append(coord)
            
            if i > 0:
                prev_node = path_nodes[i - 1]
                edge_data = self.graph.get_edge_data(prev_node, node_id)
                if edge_data:
                    total_distance += edge_data.get('distance', 0)
                    total_weight += edge_data.get('weight', 0)
                
                # 조기 종료: 최대 거리 초과 시 중단
                if total_distance > max_distance:
                    return PathResult(is_reachable=False, ...)
        
        return PathResult(
            target_pole_id=target_pole.id,
            path_coords=path_coords,
            total_distance=total_distance,
            total_weight=total_weight,
            is_reachable=True
        )
```

### 3.3 경로 탐색 흐름

```python
# pathfinder.py - 전체 경로 탐색 흐름
def find_paths(self, target_poles: List[TargetPole], max_paths=10):
    result = PathfindingResult(consumer_coord=self.consumer_coord)
    paths = []
    
    # 1. Fast Track 경로 먼저 체크 (50m 이내 직접 연결)
    fast_track_targets = [t for t in target_poles if t.is_fast_track]
    if fast_track_targets:
        target = fast_track_targets[0]
        fast_track_path = PathResult(
            path_coords=[consumer_coord, target.coord],
            total_distance=target.distance_to_consumer,
            is_fast_track=True
        )
        result.fast_track_path = fast_track_path
        paths.append(fast_track_path)
    
    # 2. 후보 전주를 직선 거리순으로 정렬 (조기 종료 최적화)
    sorted_targets = sorted(
        [t for t in target_poles if not t.is_fast_track],
        key=lambda t: t.distance_to_consumer
    )
    
    # 3. 각 전주에 대해 A* 경로 탐색
    for target in sorted_targets:
        pole_node_id = f"POLE_{target.id}"
        
        if pole_node_id not in self.graph:
            continue
        
        # A* 알고리즘 적용
        path_result = self._astar_path(
            self.consumer_node_id,
            pole_node_id,
            target,
            max_distance=400  # 최대 400m
        )
        
        if path_result and path_result.is_reachable:
            if path_result.total_distance <= 400:
                paths.append(path_result)
    
    # 4. 가중치(비용) 순으로 정렬
    paths.sort(key=lambda p: p.total_weight)
    
    # 5. 상위 N개만 반환
    result.paths = paths[:max_paths]
    return result
```

### 3.4 A* vs Dijkstra 비교

| 항목 | Dijkstra | A* |
|------|----------|-----|
| 탐색 방식 | 모든 방향 동일 탐색 | 목표 방향 우선 탐색 |
| 시간 복잡도 | O((V+E)logV) | O(bᵈ) ~ O((V+E)logV) |
| 휴리스틱 | 없음 | 유클리드 거리 |
| 조기 종료 | 불가 | 가능 |
| 적용 결과 | 기준선 | **30~50% 성능 향상** |

---

## 4. 후보 전주 선별 로직

### 4.1 Phase Matching

단상/3상 요청에 따라 적합한 전주만 후보로 선별한다.

```python
# target_selector.py - Phase Matching
def _phase_matching(self, phase_code: str) -> List[Pole]:
    if phase_code == "3":
        # 3상 요청: 고압 3상 선로가 연결된 전주만 (필수)
        return self._get_three_phase_connected_poles()
    else:
        # 단상 요청: 고압/저압 모두 허용
        return self._get_single_phase_connectable_poles()

def _get_three_phase_connected_poles(self) -> List[Pole]:
    """3상 고압선에 연결된 전주만 반환"""
    three_phase_hv_pole_ids = set()
    
    for line in self.lines:
        # 반드시 고압선(HV)이면서 3상인 경우만
        if line.is_high_voltage and line.phase_code == "3":
            if line.start_pole_id:
                three_phase_hv_pole_ids.add(line.start_pole_id)
            if line.end_pole_id:
                three_phase_hv_pole_ids.add(line.end_pole_id)
    
    return [p for p in self.poles if p.id in three_phase_hv_pole_ids]
```

### 4.2 우선순위 설정

```python
# target_selector.py - 우선순위 로직
def select(self, consumer_coord, phase_code):
    # ... Phase Matching 후 ...
    
    for target in target_poles:
        # 기본 우선순위: 거리 기반
        target.priority = int(target.distance_to_consumer)
        
        # 전선 연결 타입 분석
        conn = self._analyze_pole_connections(target.pole.id)
        
        if phase_code == "1":  # 단상
            # 저압선 연결 전주 우선 (변압기 불필요)
            if conn['has_lv']:
                target.priority -= 100  # 최우선
            elif conn['has_hv'] and not conn['has_lv']:
                target.priority += 50   # 패널티
        else:  # 3상
            # 고압 3상선 연결 전주 우선
            if conn['has_hv_3phase']:
                target.priority -= 100  # 최우선
            elif conn['has_hv']:
                target.priority -= 50   # 차선
    
    # 우선순위 오름차순 정렬
    target_poles.sort(key=lambda t: (t.priority, t.distance_to_consumer))
```

---

## 5. 전선 교차 검증 (FR-05)

신설 경로가 기존 전선과 교차하면 합선/혼촉 위험이 있으므로 해당 경로는 제외한다.

```python
# line_validator.py - 전선 교차 검증
class LineValidator:
    def validate_path(self, path_coords: List[Tuple]) -> ValidationResult:
        new_path = LineString(path_coords)
        
        crossing_lines = []
        
        for line_id, line_geom, line_type in self.line_geometries:
            # 교차 여부 확인
            if new_path.intersects(line_geom):
                # 실제 교차만 체크 (접촉은 허용)
                if new_path.crosses(line_geom):
                    # 시작/끝점 교차는 허용 (연결점)
                    if self._is_endpoint_intersection(...):
                        continue
                    
                    crossing_lines.append(f"{line_id}({line_type})")
        
        is_valid = len(crossing_lines) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            crossing_lines=crossing_lines,
            message="전선 교차 없음" if is_valid else f"교차: {crossing_lines}"
        )
```

---

## 6. 문제 해결 과정

### 6.1 문제: 저압선 데이터 누락

**현상**: 단상 설계 시 가까운 저압 전주가 아닌 먼 고압 전주가 선택됨

**원인 분석**:
- 저압선(LV) 데이터가 주 전선 레이어(`AI_FAC_002`)에 없음
- 저압선 정보가 변압기/인입선 레이어(`AI_FAC_003`)에 포함되어 있음
- `TEXT_GIS_ANNXN` 필드에 "OW 22 x 3" 형태로 저장

**해결**:
```python
# preprocessor.py - 저압선 추출 로직 추가
def _extract_lv_lines_from_transformers(self, raw_transformers):
    lv_lines = []
    
    for feature in raw_transformers:
        props = feature.get("properties", {})
        text_annxn = props.get("TEXT_GIS_ANNXN", "") or ""
        
        # OW (Outdoor Wire) 포함 시 저압선
        is_lv_line = "OW" in text_annxn.upper()
        
        if is_lv_line:
            line = Line(
                id=f"LV_{line_id}",
                line_type="LV",
                ...
            )
            lv_lines.append(line)
    
    return lv_lines
```

**결과**:
- 개선 전: 경로 156.9m, 신설 전주 7개, 비용 11.6M원
- **개선 후: 경로 25.3m, 신설 전주 0개, 비용 0.9M원**

### 6.2 문제: 3상 설계 실패

**현상**: 3상 후보 전주가 있지만 "경로 없음" 오류 발생

**원인 분석**:
```
[설계 로그]
3상 후보 전주: 7개
경로 탐색 결과: 5개 경로
전선 교차 검증: 0개 통과 ← 모두 탈락

경로 제외: 52400178 - LV_52400203(LV) 교차
경로 제외: 52400176 - 52400167(HV) 교차
...
```

**결론**: 해당 좌표는 기존 전선으로 둘러싸여 있어, 3상 전주로 가는 모든 경로가 전선과 교차함. **지리적 제약**으로 설계 불가.

---

## 7. 설계 제약조건

| 제약조건 | 값 | 설명 |
|----------|-----|------|
| 최대 거리 | 400m | 수용가~기설전주 최대 거리 |
| Fast Track | 50m | 직접 연결 가능 거리 |
| 전주 간격 | 40m | 신설 전주 배치 간격 |
| 도로 접근성 | 100m | 도로에서 최대 이격 거리 |
| 전압 강하(저압) | 6% | 허용 전압 강하율 |
| 전압 강하(고압) | 3% | 허용 전압 강하율 |

---

## 8. 성과 및 결론

### 8.1 성과
- **설계 시간**: 수작업 30분 → 자동화 2초 이내
- **경로 최적화**: A* 알고리즘으로 최적 비용 경로 산출
- **제약조건 자동 검증**: 전선 교차, 건물 간섭 등 자동 체크
- **상세 견적**: 자재비/노무비/경비 포함 공사비 자동 산출

### 8.2 기술 스택
- **Backend**: Python 3.11, FastAPI, NetworkX
- **GIS**: Shapely, WFS, EPSG:3857
- **Frontend**: React, Vite, OpenLayers
- **알고리즘**: A* (휴리스틱 경로 탐색)

### 8.3 향후 개선 방향
1. **지중화 경로 지원**: 가공 불가 지역 지중 배전 설계
2. **우회 경로 생성**: 전선 교차 시 자동 우회 로직
3. **AI 학습 적용**: 과거 설계 데이터 기반 최적 경로 예측

---

**작성자**: ELBIX AIDD 개발팀  
**문서 버전**: 1.0
