package com.elbix.aidd.ui.design

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.material3.windowsizeclass.WindowSizeClass
import androidx.compose.material3.windowsizeclass.WindowWidthSizeClass
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.elbix.aidd.R
import com.elbix.aidd.domain.model.Coordinate
import com.elbix.aidd.domain.model.PhaseCode
import com.elbix.aidd.ui.adaptive.AdaptiveResultLayout
import com.elbix.aidd.ui.adaptive.AdaptiveBottomSheetScaffold
import com.elbix.aidd.ui.components.LoadingOverlay
import com.elbix.aidd.ui.design.components.CoordinateInputCard
import com.elbix.aidd.ui.design.components.PhaseSelector
import com.elbix.aidd.ui.design.components.RouteResultCard
import com.elbix.aidd.ui.design.components.RouteResultList

/**
 * 배전 설계 화면
 * - 좌표 입력
 * - 상 선택 (단상/3상)
 * - 설계 요청 및 결과 표시
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DesignScreen(
    windowSizeClass: WindowSizeClass,
    initialCoord: String?,
    viewModel: DesignViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    val isExpanded = windowSizeClass.widthSizeClass == WindowWidthSizeClass.Expanded
    
    // 초기 좌표 설정
    LaunchedEffect(initialCoord) {
        initialCoord?.let { coordStr ->
            viewModel.setCoordinate(coordStr)
        }
    }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(R.string.design_title)) },
                actions = {
                    // 초기화 버튼
                    if (uiState.result != null) {
                        IconButton(onClick = { viewModel.reset() }) {
                            Icon(Icons.Default.Refresh, contentDescription = "초기화")
                        }
                    }
                }
            )
        }
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
        ) {
            if (uiState.result != null) {
                // 결과 화면
                DesignResultContent(
                    windowSizeClass = windowSizeClass,
                    uiState = uiState,
                    onRouteSelect = { viewModel.selectRoute(it) }
                )
            } else {
                // 입력 화면
                DesignInputContent(
                    uiState = uiState,
                    onCoordXChange = { viewModel.updateCoordX(it) },
                    onCoordYChange = { viewModel.updateCoordY(it) },
                    onPhaseChange = { viewModel.updatePhaseCode(it) },
                    onSubmit = { viewModel.submitDesign() },
                    isExpanded = isExpanded
                )
            }
            
            // 로딩 오버레이
            if (uiState.isLoading) {
                LoadingOverlay(message = stringResource(R.string.design_processing))
            }
            
            // 에러 스낵바
            uiState.errorMessage?.let { message ->
                Snackbar(
                    modifier = Modifier
                        .align(Alignment.BottomCenter)
                        .padding(16.dp),
                    action = {
                        TextButton(onClick = { viewModel.clearError() }) {
                            Text("닫기")
                        }
                    }
                ) {
                    Text(message)
                }
            }
        }
    }
}

/**
 * 설계 입력 화면 컨텐츠
 */
@Composable
private fun DesignInputContent(
    uiState: DesignUiState,
    onCoordXChange: (String) -> Unit,
    onCoordYChange: (String) -> Unit,
    onPhaseChange: (PhaseCode) -> Unit,
    onSubmit: () -> Unit,
    isExpanded: Boolean
) {
    val scrollState = rememberScrollState()
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(scrollState)
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // 안내 텍스트
        Card(
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.primaryContainer
            )
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(
                    imageVector = Icons.Default.Info,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.onPrimaryContainer
                )
                Text(
                    text = "수용가 위치를 입력하고 신청 규격을 선택한 후 설계를 요청하세요.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onPrimaryContainer
                )
            }
        }
        
        // 좌표 입력 카드
        CoordinateInputCard(
            coordX = uiState.coordX,
            coordY = uiState.coordY,
            onCoordXChange = onCoordXChange,
            onCoordYChange = onCoordYChange,
            isExpanded = isExpanded
        )
        
        // 상 선택
        PhaseSelector(
            selectedPhase = uiState.phaseCode,
            onPhaseSelect = onPhaseChange
        )
        
        Spacer(modifier = Modifier.weight(1f))
        
        // 설계 요청 버튼
        Button(
            onClick = onSubmit,
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp),
            enabled = uiState.isValidInput && !uiState.isLoading
        ) {
            Icon(
                imageVector = Icons.Default.Build,
                contentDescription = null,
                modifier = Modifier.size(20.dp)
            )
            Spacer(Modifier.width(8.dp))
            Text(
                text = stringResource(R.string.design_request),
                style = MaterialTheme.typography.titleMedium
            )
        }
    }
}

/**
 * 설계 결과 화면 컨텐츠
 */
@Composable
private fun DesignResultContent(
    windowSizeClass: WindowSizeClass,
    uiState: DesignUiState,
    onRouteSelect: (Int) -> Unit
) {
    val result = uiState.result ?: return
    val isExpanded = windowSizeClass.widthSizeClass == WindowWidthSizeClass.Expanded
    
    if (isExpanded) {
        // 펼친 상태: 듀얼 패널
        AdaptiveResultLayout(
            windowSizeClass = windowSizeClass,
            routeListContent = {
                RouteResultList(
                    routes = result.routes,
                    selectedIndex = uiState.selectedRouteIndex,
                    onRouteSelect = onRouteSelect
                )
            },
            mapContent = {
                // 지도에 선택된 경로 표시
                DesignResultMap(
                    result = result,
                    selectedRouteIndex = uiState.selectedRouteIndex
                )
            },
            bottomInfoContent = {
                // 선택된 경로 상세 정보
                result.routes.getOrNull(uiState.selectedRouteIndex)?.let { route ->
                    SelectedRouteInfoBar(route = route)
                }
            }
        )
    } else {
        // 접은 상태: 바텀시트
        AdaptiveBottomSheetScaffold(
            sheetContent = {
                // 경로 목록
                Text(
                    text = "설계 결과 (${result.routes.size}개 경로)",
                    style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier.padding(vertical = 8.dp)
                )
                
                RouteResultList(
                    routes = result.routes,
                    selectedIndex = uiState.selectedRouteIndex,
                    onRouteSelect = onRouteSelect,
                    modifier = Modifier.heightIn(max = 400.dp)
                )
            },
            sheetPeekHeight = 150
        ) { paddingValues ->
            // 지도
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
            ) {
                DesignResultMap(
                    result = result,
                    selectedRouteIndex = uiState.selectedRouteIndex
                )
            }
        }
    }
}

/**
 * 설계 결과 지도 (임시 구현)
 */
@Composable
private fun DesignResultMap(
    result: com.elbix.aidd.domain.model.DesignResult,
    selectedRouteIndex: Int
) {
    // TODO: MapLibre로 실제 경로 표시
    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Icon(
                imageVector = Icons.Default.Map,
                contentDescription = null,
                modifier = Modifier.size(64.dp),
                tint = MaterialTheme.colorScheme.primary
            )
            Text(
                text = "경로 ${selectedRouteIndex + 1} 표시 중",
                style = MaterialTheme.typography.bodyLarge
            )
            
            result.routes.getOrNull(selectedRouteIndex)?.let { route ->
                Text(
                    text = "거리: ${route.formattedDistance}m",
                    style = MaterialTheme.typography.bodyMedium
                )
                Text(
                    text = "신설 전주: ${route.newPolesCount}개",
                    style = MaterialTheme.typography.bodyMedium
                )
            }
        }
    }
}

/**
 * 선택된 경로 정보 바
 */
@Composable
private fun SelectedRouteInfoBar(
    route: com.elbix.aidd.domain.model.RouteResult
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp),
        horizontalArrangement = Arrangement.SpaceEvenly
    ) {
        InfoItem(
            label = "순위",
            value = "${route.rank}위"
        )
        InfoItem(
            label = "공사비",
            value = "${route.formattedCost}원"
        )
        InfoItem(
            label = "거리",
            value = "${route.formattedDistance}m"
        )
        InfoItem(
            label = "신설 전주",
            value = "${route.newPolesCount}개"
        )
        route.voltageDrop?.let { vd ->
            InfoItem(
                label = "전압 강하",
                value = "${vd.formattedPercent}%",
                isWarning = !vd.isAcceptable
            )
        }
    }
}

@Composable
private fun InfoItem(
    label: String,
    value: String,
    isWarning: Boolean = false
) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Text(
            text = value,
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
            color = if (isWarning) MaterialTheme.colorScheme.error 
                   else MaterialTheme.colorScheme.onSurface
        )
    }
}
