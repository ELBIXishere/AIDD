package com.elbix.aidd.ui.main

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.material3.windowsizeclass.WindowSizeClass
import androidx.compose.material3.windowsizeclass.WindowWidthSizeClass
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.elbix.aidd.R
import com.elbix.aidd.domain.model.BoundingBox
import com.elbix.aidd.domain.model.Coordinate
import com.elbix.aidd.ui.components.LoadingOverlay
import com.elbix.aidd.ui.main.components.*
import com.elbix.aidd.ui.map.components.MapLibreView
import kotlinx.coroutines.launch

/**
 * 통합 메인 화면
 * - 지도 (항상 전체 화면)
 * - 제어 패널 (좌측 또는 바텀시트)
 * - 결과 패널 (우측, 결과 있을 때)
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen(
    windowSizeClass: WindowSizeClass,
    viewModel: MainViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    val scope = rememberCoroutineScope()
    
    // 바텀시트 상태
    val bottomSheetState = rememberModalBottomSheetState(
        skipPartiallyExpanded = false
    )
    var showBottomSheet by remember { mutableStateOf(false) }
    
    // 화면 크기에 따른 레이아웃 결정
    val isExpanded = windowSizeClass.widthSizeClass >= WindowWidthSizeClass.Medium
    
    // 스낵바 호스트
    val snackbarHostState = remember { SnackbarHostState() }
    
    // 에러 메시지 표시
    LaunchedEffect(uiState.errorMessage) {
        uiState.errorMessage?.let { message ->
            snackbarHostState.showSnackbar(
                message = message,
                duration = SnackbarDuration.Short
            )
            viewModel.clearError()
        }
    }
    
    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
        // 모바일에서만 플로팅 버튼 표시
        floatingActionButton = {
            if (!isExpanded) {
                FloatingActionButton(
                    onClick = { showBottomSheet = true }
                ) {
                    Icon(Icons.Default.Menu, contentDescription = "메뉴 열기")
                }
            }
        }
    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            if (isExpanded) {
                // 태블릿/폴더블 레이아웃: 좌측 제어패널 | 지도 | 우측 결과패널
                ExpandedLayout(
                    uiState = uiState,
                    viewModel = viewModel
                )
            } else {
                // 모바일 레이아웃: 지도 전체 + 바텀시트
                CompactLayout(
                    uiState = uiState,
                    viewModel = viewModel
                )
            }
            
            // 설계 로딩 오버레이
            if (uiState.isDesignLoading) {
                LoadingOverlay(
                    message = stringResource(R.string.design_processing)
                )
            }
        }
        
        // 모바일 바텀시트
        if (showBottomSheet && !isExpanded) {
            ControlBottomSheet(
                sheetState = bottomSheetState,
                // 좌표 입력
                coordX = uiState.coordX,
                coordY = uiState.coordY,
                phaseCode = uiState.phaseCode,
                isValidInput = uiState.isValidInput,
                onCoordXChange = viewModel::updateCoordX,
                onCoordYChange = viewModel::updateCoordY,
                onPhaseCodeChange = viewModel::updatePhaseCode,
                // 설계
                isDesignLoading = uiState.isDesignLoading,
                designResult = uiState.designResult,
                selectedRouteIndex = uiState.selectedRouteIndex,
                onSubmitDesign = viewModel::submitDesign,
                onRouteSelect = viewModel::selectRoute,
                onClearResult = viewModel::clearDesignResult,
                // 시설물
                showFacilities = uiState.showFacilities,
                layerVisibility = uiState.layerVisibility,
                onFacilitiesToggle = viewModel::toggleFacilitiesVisible,
                onLayerToggle = viewModel::toggleLayer,
                onRefreshFacilities = viewModel::refreshFacilities,
                // 테스트 좌표
                onMoveToCoordinate = { coord ->
                    viewModel.moveToCoordinate(coord)
                    scope.launch { bottomSheetState.hide() }
                    showBottomSheet = false
                },
                // 시트 닫기
                onDismiss = { showBottomSheet = false }
            )
        }
    }
}

/**
 * 확장 레이아웃 (태블릿/폴더블)
 */
@Composable
private fun ExpandedLayout(
    uiState: MainUiState,
    viewModel: MainViewModel
) {
    Row(modifier = Modifier.fillMaxSize()) {
        // 좌측 제어 패널 (240dp)
        Surface(
            modifier = Modifier.width(240.dp),
            tonalElevation = 2.dp
        ) {
            ControlPanel(
                coordX = uiState.coordX,
                coordY = uiState.coordY,
                phaseCode = uiState.phaseCode,
                showFacilities = uiState.showFacilities,
                layerVisibility = uiState.layerVisibility,
                isValidInput = uiState.isValidInput,
                isDesignLoading = uiState.isDesignLoading,
                onCoordXChange = viewModel::updateCoordX,
                onCoordYChange = viewModel::updateCoordY,
                onPhaseCodeChange = viewModel::updatePhaseCode,
                onFacilitiesToggle = viewModel::toggleFacilitiesVisible,
                onLayerToggle = viewModel::toggleLayer,
                onRefreshFacilities = viewModel::refreshFacilities,
                onMoveToCoordinate = viewModel::moveToCoordinate,
                onSubmitDesign = viewModel::submitDesign,
                onClearCoord = viewModel::clearCoordinate
            )
        }
        
        // 중앙 지도
        Box(modifier = Modifier.weight(1f)) {
            MainMapView(
                uiState = uiState,
                viewModel = viewModel
            )
        }
        
        // 우측 결과 패널 (설계 결과 있을 때만, 300dp)
        if (uiState.hasDesignResult) {
            uiState.designResult?.let { result ->
                ResultPanel(
                    modifier = Modifier.width(300.dp),
                    result = result,
                    selectedRouteIndex = uiState.selectedRouteIndex,
                    onRouteSelect = viewModel::selectRoute,
                    onClose = viewModel::clearDesignResult
                )
            }
        }
    }
}

/**
 * 컴팩트 레이아웃 (모바일)
 */
@Composable
private fun CompactLayout(
    uiState: MainUiState,
    viewModel: MainViewModel
) {
    Box(modifier = Modifier.fillMaxSize()) {
        // 지도 전체 화면
        MainMapView(
            uiState = uiState,
            viewModel = viewModel
        )
        
        // 상단 컨트롤 바
        TopControlBar(
            modifier = Modifier
                .align(Alignment.TopCenter)
                .padding(16.dp),
            showFacilities = uiState.showFacilities,
            onFacilitiesToggle = viewModel::toggleFacilitiesVisible,
            onRefreshFacilities = viewModel::refreshFacilities
        )
    }
}

/**
 * 메인 지도 뷰 (시설물 + 설계 경로)
 */
@Composable
private fun MainMapView(
    uiState: MainUiState,
    viewModel: MainViewModel
) {
    // 기본 지도 + 시설물 + 설계 경로
    MapLibreView(
        modifier = Modifier.fillMaxSize(),
        facilities = if (uiState.showFacilities) uiState.facilities else null,
        layerVisibility = uiState.layerVisibility,
        selectedCoordinate = uiState.selectedCoord,
        moveToCoordinate = uiState.mapMoveRequest,
        designResult = uiState.designResult,  // 설계 결과 전달
        selectedRouteIndex = uiState.selectedRouteIndex,  // 선택된 경로 인덱스
        onMapClick = { coord ->
            viewModel.selectCoordinate(coord)
        },
        onMapLongClick = { coord ->
            viewModel.selectCoordinate(coord)
        },
        onCameraMove = { bbox ->
            viewModel.loadFacilities(bbox)
        },
        onMoveCompleted = viewModel::onMapMoveCompleted
    )
}

/**
 * 상단 컨트롤 바 (모바일용)
 */
@Composable
private fun TopControlBar(
    modifier: Modifier = Modifier,
    showFacilities: Boolean,
    onFacilitiesToggle: (Boolean) -> Unit,
    onRefreshFacilities: () -> Unit
) {
    Card(
        modifier = modifier,
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Row(
            modifier = Modifier.padding(8.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            FilterChip(
                selected = showFacilities,
                onClick = { onFacilitiesToggle(!showFacilities) },
                label = { Text("시설물") },
                leadingIcon = if (showFacilities) {
                    { Icon(Icons.Default.Check, contentDescription = null, modifier = Modifier.size(18.dp)) }
                } else null
            )
            
            IconButton(
                onClick = onRefreshFacilities,
                enabled = showFacilities,
                modifier = Modifier.size(36.dp)
            ) {
                Icon(
                    Icons.Default.Refresh,
                    contentDescription = "새로고침",
                    modifier = Modifier.size(20.dp)
                )
            }
        }
    }
}
