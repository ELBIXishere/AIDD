# ELBIX AIDD

**AI 기반 배전 설계 자동화 및 공사비 최적 경로 추천 시스템**

## 개요

수용가(건물)의 전력 신청 정보를 기반으로 GIS 공간 정보와 한전 설비 데이터를 분석하여, 전기적/지리적 제약사항을 준수하면서 공사비가 가장 저렴한 최적의 배전 설계안을 자동으로 도출하는 백엔드 엔진입니다.

## 주요 기능

- **자동화**: 수동 설계 과정을 알고리즘화하여 설계 소요 시간 단축
- **규격 준수**: 3상/단상 등 수용가 요청 규격에 맞는 전원(기설전주) 자동 선별
- **비용 최적화**: 신설 전주 최소화 및 표준 공사비를 반영한 경제적 경로 추천
- **규정 준수**: 도로 중심선 활용, 건물 회피, 최대 거리(400m) 제한 등 설계 기준 반영

## 기술 스택

- **Framework**: FastAPI 0.100+
- **HTTP Client**: httpx 0.24+
- **좌표 변환**: pyproj 3.6+
- **기하 연산**: Shapely 2.0+
- **그래프**: NetworkX 3.1+

## 설치 및 실행

### 로컬 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# 서버 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker 실행

```bash
# 이미지 빌드
docker build -t elbix-aidd .

# 컨테이너 실행
docker run -d -p 8000:8000 --name elbix_aidd elbix-aidd
```

## API 사용법

### POST /api/v1/design

배전 설계 요청

```json
{
  "code": "coord",
  "coord": "14241940.817790061,4437601.6755945515",
  "phase_code": "3"
}
```

### 응답 예시

```json
{
  "status": "Success",
  "request_spec": "3상",
  "routes": [
    {
      "rank": 1,
      "total_cost": 1500000,
      "total_distance": 120.5,
      "start_pole_id": "POLE_12345",
      "new_poles_count": 3,
      "path_coordinates": [[x1, y1], [x2, y2]],
      "new_pole_coordinates": [[px1, py1], [px2, py2]]
    }
  ]
}
```

## 프로젝트 구조

```
elbix_aidd/
├── app/
│   ├── main.py           # FastAPI 앱 진입점
│   ├── config.py         # 설정 관리
│   ├── api/              # API 엔드포인트
│   ├── core/             # 핵심 로직
│   ├── models/           # Pydantic 모델
│   └── utils/            # 유틸리티
├── tests/                # 테스트
├── requirements.txt
├── Dockerfile
└── README.md
```

## 라이선스

Proprietary - ELBIX
