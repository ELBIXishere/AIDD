package com.elbix.aidd.ui.facilities

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
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.elbix.aidd.R
import com.elbix.aidd.domain.model.*
import com.elbix.aidd.ui.adaptive.AdaptiveFacilitiesLayout
import com.elbix.aidd.ui.components.LoadingOverlay
import com.elbix.aidd.ui.main.LayerVisibility
import com.elbix.aidd.ui.main.MapLayer
import com.elbix.aidd.ui.map.components.MapLibreView

/**
 * 시설물 조회 화면
 * - 영역별 시설물 조회
 * - 레이어별 표시/숨김
 * - 시설물 상세 정보 표시
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FacilitiesScreen(
    windowSizeClass: WindowSizeClass,
    viewModel: FacilitiesViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    val isExpanded = windowSizeClass.widthSizeClass == WindowWidthSizeClass.Expanded
    
    var showFilterSheet by remember { mutableStateOf(false) }
    var selectedFacility by remember { mutableStateOf<Any?>(null) }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("시설물 조회") },
                actions = {
                    // 필터 버튼 (접힌 상태에서만)
                    if (!isExpanded) {
                        IconButton(onClick = { showFilterSheet = true }) {
                            Badge(
                                modifier = Modifier.offset(x = 8.dp, y = (-8).dp)
                            ) {
                                Text(uiState.activeLayerCount.toString())
                            }
                            Icon(Icons.Default.FilterList, contentDescription = "필터")
                        }
                    }
                    
                    // 새로고침 버튼
                    IconButton(
                        onClick = { viewModel.refresh() },
                        enabled = !uiState.isLoading
                    ) {
                        Icon(Icons.Default.Refresh, contentDescription = "새로고침")
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
            AdaptiveFacilitiesLayout(
                windowSizeClass = windowSizeClass,
                filterContent = {
                    // 필터 패널
                    FacilitiesFilterPanel(
                        layerVisibility = uiState.layerVisibility,
                        facilitiesCount = uiState.facilitiesCount,
                        onLayerToggle = { layer, visible ->
                            viewModel.toggleLayer(layer, visible)
                        }
                    )
                },
                mapContent = {
                    // 지도
                    MapLibreView(
                        modifier = Modifier.fillMaxSize(),
                        facilities = uiState.facilities,
                        layerVisibility = uiState.layerVisibility,
                        selectedCoordinate = null,
                        onMapClick = { coord ->
                            // 시설물 선택 처리
                        },
                        onMapLongClick = { },
                        onCameraMove = { bbox ->
                            viewModel.loadFacilities(bbox)
                        }
                    )
                    
                    // 시설물 개수 표시 (좌상단)
                    Surface(
                        modifier = Modifier
                            .align(Alignment.TopStart)
                            .padding(16.dp),
                        shape = MaterialTheme.shapes.medium,
                        color = MaterialTheme.colorScheme.surface,
                        tonalElevation = 4.dp
                    ) {
                        FacilitiesCountBadge(count = uiState.facilitiesCount)
                    }
                }
            )
            
            // 로딩 인디케이터
            if (uiState.isLoading) {
                CircularProgressIndicator(
                    modifier = Modifier
                        .align(Alignment.Center)
                        .size(48.dp)
                )
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
    
    // 필터 바텀시트 (접힌 상태)
    if (showFilterSheet) {
        ModalBottomSheet(onDismissRequest = { showFilterSheet = false }) {
            FacilitiesFilterPanel(
                layerVisibility = uiState.layerVisibility,
                facilitiesCount = uiState.facilitiesCount,
                onLayerToggle = { layer, visible ->
                    viewModel.toggleLayer(layer, visible)
                },
                modifier = Modifier.padding(bottom = 32.dp)
            )
        }
    }
}

/**
 * 필터 패널
 */
@Composable
private fun FacilitiesFilterPanel(
    layerVisibility: LayerVisibility,
    facilitiesCount: FacilitiesCount,
    onLayerToggle: (MapLayer, Boolean) -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .padding(16.dp)
            .verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Text(
            text = "레이어 설정",
            style = MaterialTheme.typography.titleMedium,
            modifier = Modifier.padding(bottom = 8.dp)
        )
        
        // 전주 레이어
        LayerToggleItem(
            icon = Icons.Default.ElectricBolt,
            label = stringResource(R.string.map_layer_poles),
            count = facilitiesCount.poles,
            isChecked = layerVisibility.poles,
            onCheckedChange = { onLayerToggle(MapLayer.POLES, it) }
        )
        
        // 전선 레이어
        LayerToggleItem(
            icon = Icons.Default.Cable,
            label = stringResource(R.string.map_layer_lines),
            count = facilitiesCount.lines,
            isChecked = layerVisibility.lines,
            onCheckedChange = { onLayerToggle(MapLayer.LINES, it) }
        )
        
        // 변압기 레이어
        LayerToggleItem(
            icon = Icons.Default.Transform,
            label = stringResource(R.string.map_layer_transformers),
            count = facilitiesCount.transformers,
            isChecked = layerVisibility.transformers,
            onCheckedChange = { onLayerToggle(MapLayer.TRANSFORMERS, it) }
        )
        
        Divider(modifier = Modifier.padding(vertical = 8.dp))
        
        Text(
            text = "배경 레이어",
            style = MaterialTheme.typography.titleSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        
        // 도로 레이어
        LayerToggleItem(
            icon = Icons.Default.Route,
            label = stringResource(R.string.map_layer_roads),
            count = facilitiesCount.roads,
            isChecked = layerVisibility.roads,
            onCheckedChange = { onLayerToggle(MapLayer.ROADS, it) }
        )
        
        // 건물 레이어
        LayerToggleItem(
            icon = Icons.Default.Home,
            label = stringResource(R.string.map_layer_buildings),
            count = facilitiesCount.buildings,
            isChecked = layerVisibility.buildings,
            onCheckedChange = { onLayerToggle(MapLayer.BUILDINGS, it) }
        )
    }
}

/**
 * 레이어 토글 아이템
 */
@Composable
private fun LayerToggleItem(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    label: String,
    count: Int,
    isChecked: Boolean,
    onCheckedChange: (Boolean) -> Unit
) {
    Surface(
        onClick = { onCheckedChange(!isChecked) },
        shape = MaterialTheme.shapes.medium,
        color = if (isChecked) {
            MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.3f)
        } else {
            MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
        }
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(
                    imageVector = icon,
                    contentDescription = null,
                    tint = if (isChecked) {
                        MaterialTheme.colorScheme.primary
                    } else {
                        MaterialTheme.colorScheme.onSurfaceVariant
                    }
                )
                Column {
                    Text(
                        text = label,
                        style = MaterialTheme.typography.bodyLarge
                    )
                    Text(
                        text = "${count}개",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
            
            Switch(
                checked = isChecked,
                onCheckedChange = onCheckedChange
            )
        }
    }
}

/**
 * 시설물 개수 배지
 */
@Composable
private fun FacilitiesCountBadge(
    count: FacilitiesCount
) {
    Row(
        modifier = Modifier.padding(12.dp),
        horizontalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        CountItem(
            icon = Icons.Default.ElectricBolt,
            count = count.poles
        )
        CountItem(
            icon = Icons.Default.Cable,
            count = count.lines
        )
        CountItem(
            icon = Icons.Default.Transform,
            count = count.transformers
        )
    }
}

@Composable
private fun CountItem(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    count: Int
) {
    Row(
        horizontalArrangement = Arrangement.spacedBy(4.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Icon(
            imageVector = icon,
            contentDescription = null,
            modifier = Modifier.size(16.dp),
            tint = MaterialTheme.colorScheme.primary
        )
        Text(
            text = count.toString(),
            style = MaterialTheme.typography.labelMedium
        )
    }
}
