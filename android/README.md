# ELBIX AIDD Android App

AI 기반 배전 설계 자동화 시스템의 Android 클라이언트 앱입니다.

## 주요 기능

### 1. 지도 기반 시설물 조회
- 전주, 전선, 변압기, 도로, 건물 레이어 표시
- 레이어별 On/Off 토글
- 실시간 영역 기반 데이터 조회

### 2. 배전 설계 요청
- 지도에서 수용가 위치 선택 (탭/길게 누르기)
- 단상/3상 규격 선택
- 설계 요청 및 결과 확인

### 3. 설계 결과 시각화
- 추천 경로 지도 위에 표시 (순위별 색상 구분)
- 신설 전주 위치 마커
- 공사비, 전압강하, 거리 정보 카드
- 상세 비용 내역 확인

### 4. 폴더블 디바이스 지원
- Galaxy Z Fold 시리즈 최적화
- 접힌 상태: 단일 패널 + 바텀시트
- 펼친 상태: 듀얼 패널 레이아웃

## 기술 스택

- **언어**: Kotlin 1.9
- **UI**: Jetpack Compose + Material3
- **폴더블**: Jetpack WindowManager
- **지도**: MapLibre GL
- **네트워크**: Retrofit2 + OkHttp
- **DI**: Hilt
- **비동기**: Kotlin Coroutines + Flow
- **아키텍처**: MVVM + Clean Architecture

## 프로젝트 구조

```
app/src/main/java/com/elbix/aidd/
├── data/               # 데이터 레이어
│   ├── api/           # Retrofit API 서비스
│   ├── model/         # DTO 모델
│   ├── mapper/        # DTO ↔ Domain 매퍼
│   └── repository/    # Repository 구현체
├── domain/            # 도메인 레이어
│   ├── model/         # 도메인 모델
│   ├── repository/    # Repository 인터페이스
│   └── usecase/       # UseCase
├── di/                # Hilt 모듈
├── ui/                # UI 레이어
│   ├── adaptive/      # 폴더블 대응 레이아웃
│   ├── components/    # 공통 컴포넌트
│   ├── design/        # 설계 화면
│   ├── facilities/    # 시설물 조회 화면
│   ├── map/           # 지도 화면
│   ├── navigation/    # 네비게이션
│   ├── settings/      # 설정 화면
│   └── theme/         # 테마
└── util/              # 유틸리티
```

## 빌드 및 실행

### 요구사항
- Android Studio Hedgehog (2023.1.1) 이상
- JDK 17
- Android SDK 34
- Gradle 8.5

### 빌드
```bash
cd android
./gradlew assembleDebug
```

### API 서버 설정
`app/build.gradle.kts`에서 API_BASE_URL 수정:
```kotlin
buildConfigField("String", "API_BASE_URL", "\"http://your-server:8000/\"")
```

## 화면 구성

### 1. 지도 화면 (메인)
- 기본 진입 화면
- 지도 탭으로 위치 선택
- 길게 눌러서 설계 요청으로 이동

### 2. 설계 화면
- 좌표 입력 (EPSG:3857)
- 단상/3상 선택
- 설계 결과 목록 및 지도 표시

### 3. 시설물 화면
- 영역 내 시설물 조회
- 레이어별 필터링

### 4. 설정 화면
- API 서버 설정
- 앱 정보

## 폴더블 대응

### Galaxy Z Fold 7 최적화
- 접힌 상태 (커버 스크린): 단일 패널 UI
- 펼친 상태 (메인 스크린): 듀얼 패널 UI
- 화면 연속성 지원

### WindowSizeClass 기반 분기
```kotlin
when (windowSizeClass.widthSizeClass) {
    WindowWidthSizeClass.Compact -> SinglePaneLayout()
    WindowWidthSizeClass.Medium -> SinglePaneLayout()
    WindowWidthSizeClass.Expanded -> DualPaneLayout()
}
```

## 라이선스

ELBIX AIDD는 내부 프로젝트입니다.
