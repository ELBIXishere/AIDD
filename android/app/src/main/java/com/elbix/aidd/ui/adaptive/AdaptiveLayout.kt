package com.elbix.aidd.ui.adaptive

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.material3.windowsizeclass.WindowSizeClass
import androidx.compose.material3.windowsizeclass.WindowWidthSizeClass
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

/**
 * 적응형 레이아웃 - 폴더블 디바이스 대응
 * 
 * 화면 크기에 따른 레이아웃:
 * - Compact (접힘): 단일 패널
 * - Medium: 단일 패널 + 확장 가능 시트
 * - Expanded (펼침): 듀얼 패널 (1:2 비율)
 */
@Composable
fun AdaptiveLayout(
    windowSizeClass: WindowSizeClass,
    listContent: @Composable () -> Unit,
    detailContent: @Composable () -> Unit,
    modifier: Modifier = Modifier
) {
    when (windowSizeClass.widthSizeClass) {
        WindowWidthSizeClass.Compact -> {
            // 접은 상태: 단일 패널 (detailContent만 표시)
            // 리스트는 별도 화면이나 바텀시트로 처리
            Box(modifier = modifier.fillMaxSize()) {
                detailContent()
            }
        }
        WindowWidthSizeClass.Medium -> {
            // 중간 크기: 단일 패널
            Box(modifier = modifier.fillMaxSize()) {
                detailContent()
            }
        }
        WindowWidthSizeClass.Expanded -> {
            // 펼친 상태: 듀얼 패널 (리스트 1/3 + 상세 2/3)
            DualPaneLayout(
                modifier = modifier,
                listContent = listContent,
                detailContent = detailContent
            )
        }
    }
}

/**
 * 세로 구분선 (VerticalDivider 대체)
 */
@Composable
private fun VerticalDividerCustom() {
    Box(
        modifier = Modifier
            .fillMaxHeight()
            .width(1.dp)
            .background(MaterialTheme.colorScheme.outlineVariant)
    )
}

/**
 * 듀얼 패널 레이아웃
 * - 좌측: 리스트/목록 패널 (1/3)
 * - 우측: 상세/지도 패널 (2/3)
 */
@Composable
fun DualPaneLayout(
    modifier: Modifier = Modifier,
    listContent: @Composable () -> Unit,
    detailContent: @Composable () -> Unit
) {
    Row(modifier = modifier.fillMaxSize()) {
        // 좌측 패널 (리스트) - 1/3 너비
        Surface(
            modifier = Modifier
                .weight(1f)
                .fillMaxHeight(),
            color = MaterialTheme.colorScheme.surfaceVariant,
            tonalElevation = 1.dp
        ) {
            listContent()
        }
        
        // 구분선
        VerticalDividerCustom()
        
        // 우측 패널 (상세/지도) - 2/3 너비
        Box(
            modifier = Modifier
                .weight(2f)
                .fillMaxHeight()
        ) {
            detailContent()
        }
    }
}

/**
 * 적응형 결과 레이아웃
 * - 설계 결과 화면용
 * - 경로 목록 + 지도 표시
 */
@Composable
fun AdaptiveResultLayout(
    windowSizeClass: WindowSizeClass,
    routeListContent: @Composable () -> Unit,
    mapContent: @Composable () -> Unit,
    bottomInfoContent: @Composable () -> Unit,
    modifier: Modifier = Modifier
) {
    when (windowSizeClass.widthSizeClass) {
        WindowWidthSizeClass.Expanded -> {
            // 펼친 상태: 수평 분할
            Column(modifier = modifier.fillMaxSize()) {
                Row(modifier = Modifier.weight(1f)) {
                    // 좌측: 경로 목록
                    Surface(
                        modifier = Modifier
                            .weight(1f)
                            .fillMaxHeight(),
                        tonalElevation = 1.dp
                    ) {
                        routeListContent()
                    }
                    
                    VerticalDividerCustom()
                    
                    // 우측: 지도
                    Box(
                        modifier = Modifier
                            .weight(2f)
                            .fillMaxHeight()
                    ) {
                        mapContent()
                    }
                }
                
                // 하단 정보 바
                Divider()
                Surface(tonalElevation = 2.dp) {
                    bottomInfoContent()
                }
            }
        }
        else -> {
            // 접은 상태: 수직 분할 (지도 + 바텀시트)
            Box(modifier = modifier.fillMaxSize()) {
                // 지도 (전체)
                mapContent()
                
                // 바텀시트로 경로 목록 표시는 별도 처리
            }
        }
    }
}

/**
 * 적응형 시설물 레이아웃
 * - 시설물 조회 화면용
 */
@Composable
fun AdaptiveFacilitiesLayout(
    windowSizeClass: WindowSizeClass,
    filterContent: @Composable () -> Unit,
    mapContent: @Composable () -> Unit,
    modifier: Modifier = Modifier
) {
    when (windowSizeClass.widthSizeClass) {
        WindowWidthSizeClass.Expanded -> {
            // 펼친 상태: 좌측 필터 + 우측 지도
            Row(modifier = modifier.fillMaxSize()) {
                // 좌측: 필터/레이어 설정
                Surface(
                    modifier = Modifier
                        .width(320.dp)
                        .fillMaxHeight(),
                    tonalElevation = 1.dp
                ) {
                    filterContent()
                }
                
                VerticalDividerCustom()
                
                // 우측: 지도
                Box(
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxHeight()
                ) {
                    mapContent()
                }
            }
        }
        else -> {
            // 접은 상태: 지도 전체 + 플로팅 필터 버튼
            Box(modifier = modifier.fillMaxSize()) {
                mapContent()
            }
        }
    }
}
