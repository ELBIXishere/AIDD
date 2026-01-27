# ELBIX AIDD Frontend

AI 기반 배전 설계 자동화 시스템의 프론트엔드 애플리케이션입니다.

## 기술 스택

- **Framework**: React 18 + Vite
- **Map**: OpenLayers 9 (EPSG:3857)
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios

## 설치 및 실행

### 1. 의존성 설치

```bash
cd frontend
npm install
```

### 2. 개발 서버 실행

```bash
npm run dev
```

브라우저에서 http://localhost:3000 접속

### 3. 프로덕션 빌드

```bash
npm run build
npm run preview
```

## 환경 변수

`.env` 파일을 생성하여 환경 변수를 설정할 수 있습니다:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

## 주요 기능

### 1. 지도 인터페이스
- VWorld 배경지도 (OSM 폴백)
- 클릭으로 수용가 위치 선택
- 설계 결과 경로/전주 시각화

### 2. 설계 요청
- 좌표 직접 입력 또는 지도 클릭
- 단상/3상 선택
- 설계 실행 및 결과 조회

### 3. 결과 시각화
- 경로 목록 (Rank 순)
- 경로별 상세 정보 (전주 수, 거리, 비용)
- 경로 선택 시 지도에 하이라이트

## 프로젝트 구조

```
src/
├── main.jsx              # 엔트리 포인트
├── App.jsx               # 메인 앱 컴포넌트
├── index.css             # 글로벌 스타일
├── components/
│   ├── Map/
│   │   └── MapView.jsx   # OpenLayers 지도
│   ├── Panel/
│   │   ├── ControlPanel.jsx  # 제어 패널
│   │   └── ResultPanel.jsx   # 결과 패널
│   └── common/
│       ├── Button.jsx
│       ├── Loading.jsx
│       └── Toast.jsx
├── hooks/
│   ├── useDesign.js      # 설계 API 훅
│   └── useMap.js         # 지도 유틸리티 훅
├── services/
│   └── api.js            # API 클라이언트
├── utils/
│   └── coordinate.js     # 좌표 변환 유틸리티
└── styles/
    └── map.css           # 지도 스타일
```

## API 연동

백엔드 서버가 `localhost:8000`에서 실행 중이어야 합니다.

```bash
# 백엔드 서버 실행 (프로젝트 루트에서)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 스크린샷

```
┌─────────────────────────────────────────────────────────────┐
│  ELBIX AIDD - AI 기반 배전 설계 자동화 시스템               │
├──────────────┬──────────────────────────────────────────────┤
│              │                                              │
│  [제어 패널]  │              [지도 영역]                     │
│              │                                              │
│  좌표 입력    │         ┌─────┐                             │
│  ┌─────────┐ │         │ 전주 │  ───── 경로                │
│  │ X:      │ │         └─────┘                             │
│  │ Y:      │ │              ★ 수용가                       │
│  └─────────┘ │                                              │
│              │                                              │
│  상 선택     │                                              │
│  ● 단상     │                                              │
│  ○ 3상     │                                              │
│              │                                              │
│  [설계 실행] │                                              │
│              │                                              │
├──────────────┼──────────────────────────────────────────────┤
│  [결과 패널]  │                                              │
│              │                                              │
│  Rank 1 ✓   │                                              │
│  전주: 2개   │                                              │
│  거리: 68m  │                                              │
│  비용: 20068│                                              │
└──────────────┴──────────────────────────────────────────────┘
```

## 라이선스

Private - ELBIX
