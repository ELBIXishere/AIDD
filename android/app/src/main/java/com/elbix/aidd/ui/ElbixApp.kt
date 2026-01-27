package com.elbix.aidd.ui

import androidx.compose.material3.windowsizeclass.WindowSizeClass
import androidx.compose.runtime.Composable
import com.elbix.aidd.ui.main.MainScreen

/**
 * ELBIX AIDD 메인 앱 컴포저블
 * - 단일 통합 화면 구조 (웹 프로젝트와 동일)
 * - 지도 + 제어 패널 + 결과 패널 통합
 * - 폴더블/태블릿: 좌우 패널 표시
 * - 모바일: 바텀시트 사용
 */
@Composable
fun ElbixApp(
    windowSizeClass: WindowSizeClass
) {
    // 단일 통합 화면 사용
    MainScreen(
        windowSizeClass = windowSizeClass
    )
}
