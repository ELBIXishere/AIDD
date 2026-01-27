package com.elbix.aidd.ui.map

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
import com.elbix.aidd.domain.model.Coordinate
import com.elbix.aidd.ui.components.LayerControlPanel
import com.elbix.aidd.ui.main.LayerVisibility
import com.elbix.aidd.ui.main.MapLayer
import com.elbix.aidd.ui.map.components.MapLibreView

/**
 * 지도 화면
 * - MapLibre 기반 지도 표시
 * - 시설물 레이어 표시 (전주, 전선, 변압기 등)
 * - 위치 선택 기능
 */
@Composable
fun MapScreen(
    windowSizeClass: WindowSizeClass,
    onNavigateToDesign: (String) -> Unit,
    viewModel: MapViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    val isExpanded = windowSizeClass.widthSizeClass == WindowWidthSizeClass.Expanded
    
    // 레이어 컨트롤 다이얼로그 표시 여부
    var showLayerControl by remember { mutableStateOf(false) }
    
    // 선택된 좌표
    var selectedCoordinate by remember { mutableStateOf<Coordinate?>(null) }
    
    Box(modifier = Modifier.fillMaxSize()) {
        // 지도 뷰
        MapLibreView(
            modifier = Modifier.fillMaxSize(),
            facilities = uiState.facilities,
            layerVisibility = uiState.layerVisibility,
            selectedCoordinate = selectedCoordinate,
            onMapClick = { coord ->
                selectedCoordinate = coord
            },
            onMapLongClick = { coord ->
                // 길게 누르면 설계 화면으로 이동
                selectedCoordinate = coord
                onNavigateToDesign("${coord.x},${coord.y}")
            },
            onCameraMove = { bbox ->
                // 카메라 이동 시 시설물 조회
                viewModel.loadFacilities(bbox)
            }
        )
        
        // 상단 컨트롤 바
        TopControlBar(
            modifier = Modifier
                .align(Alignment.TopCenter)
                .padding(16.dp),
            onLayerControlClick = { showLayerControl = true },
            onRefreshClick = { viewModel.refreshFacilities() },
            isLoading = uiState.isLoading
        )
        
        // 하단 정보 바 (선택된 좌표 정보)
        selectedCoordinate?.let { coord ->
            BottomInfoBar(
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .padding(16.dp),
                coordinate = coord,
                onDesignClick = {
                    onNavigateToDesign("${coord.x},${coord.y}")
                },
                onDismiss = { selectedCoordinate = null }
            )
        }
        
        // 확대/축소 버튼 (오른쪽)
        ZoomControls(
            modifier = Modifier
                .align(Alignment.CenterEnd)
                .padding(16.dp),
            onZoomIn = { /* TODO: 줌 인 */ },
            onZoomOut = { /* TODO: 줌 아웃 */ }
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
    
    // 레이어 컨트롤 다이얼로그
    if (showLayerControl) {
        LayerControlDialog(
            layerVisibility = uiState.layerVisibility,
            onLayerToggle = { layer, visible ->
                viewModel.toggleLayer(layer, visible)
            },
            onDismiss = { showLayerControl = false }
        )
    }
}

/**
 * 상단 컨트롤 바
 */
@Composable
private fun TopControlBar(
    modifier: Modifier = Modifier,
    onLayerControlClick: () -> Unit,
    onRefreshClick: () -> Unit,
    isLoading: Boolean
) {
    Row(
        modifier = modifier,
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        // 레이어 컨트롤 버튼
        FilledTonalIconButton(onClick = onLayerControlClick) {
            Icon(
                imageVector = Icons.Default.Layers,
                contentDescription = "레이어 설정"
            )
        }
        
        // 새로고침/불러오기 버튼
        FilledTonalIconButton(
            onClick = onRefreshClick,
            enabled = !isLoading
        ) {
            if (isLoading) {
                CircularProgressIndicator(
                    modifier = Modifier.size(24.dp),
                    strokeWidth = 2.dp
                )
            } else {
                Icon(
                    imageVector = Icons.Default.Refresh,
                    contentDescription = "시설물 불러오기"
                )
            }
        }
    }
}

/**
 * 하단 정보 바 (선택된 좌표)
 */
@Composable
private fun BottomInfoBar(
    modifier: Modifier = Modifier,
    coordinate: Coordinate,
    onDesignClick: () -> Unit,
    onDismiss: () -> Unit
) {
    Card(
        modifier = modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = "선택된 위치",
                    style = MaterialTheme.typography.titleSmall
                )
                Text(
                    text = String.format("X: %.2f", coordinate.x),
                    style = MaterialTheme.typography.bodySmall
                )
                Text(
                    text = String.format("Y: %.2f", coordinate.y),
                    style = MaterialTheme.typography.bodySmall
                )
            }
            
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                // 설계 요청 버튼
                FilledTonalButton(onClick = onDesignClick) {
                    Icon(
                        imageVector = Icons.Default.Build,
                        contentDescription = null,
                        modifier = Modifier.size(18.dp)
                    )
                    Spacer(Modifier.width(4.dp))
                    Text("설계 요청")
                }
                
                // 닫기 버튼
                IconButton(onClick = onDismiss) {
                    Icon(
                        imageVector = Icons.Default.Close,
                        contentDescription = "닫기"
                    )
                }
            }
        }
    }
}

/**
 * 확대/축소 컨트롤
 */
@Composable
private fun ZoomControls(
    modifier: Modifier = Modifier,
    onZoomIn: () -> Unit,
    onZoomOut: () -> Unit
) {
    Column(
        modifier = modifier,
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        FilledTonalIconButton(onClick = onZoomIn) {
            Icon(
                imageVector = Icons.Default.Add,
                contentDescription = "확대"
            )
        }
        
        FilledTonalIconButton(onClick = onZoomOut) {
            Icon(
                imageVector = Icons.Default.Remove,
                contentDescription = "축소"
            )
        }
    }
}

/**
 * 레이어 컨트롤 다이얼로그
 */
@Composable
private fun LayerControlDialog(
    layerVisibility: LayerVisibility,
    onLayerToggle: (MapLayer, Boolean) -> Unit,
    onDismiss: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("레이어 설정") },
        text = {
            Column {
                LayerToggleItem(
                    label = stringResource(R.string.map_layer_poles),
                    checked = layerVisibility.poles,
                    onCheckedChange = { onLayerToggle(MapLayer.POLES, it) }
                )
                LayerToggleItem(
                    label = stringResource(R.string.map_layer_lines),
                    checked = layerVisibility.lines,
                    onCheckedChange = { onLayerToggle(MapLayer.LINES, it) }
                )
                LayerToggleItem(
                    label = stringResource(R.string.map_layer_transformers),
                    checked = layerVisibility.transformers,
                    onCheckedChange = { onLayerToggle(MapLayer.TRANSFORMERS, it) }
                )
                LayerToggleItem(
                    label = stringResource(R.string.map_layer_roads),
                    checked = layerVisibility.roads,
                    onCheckedChange = { onLayerToggle(MapLayer.ROADS, it) }
                )
                LayerToggleItem(
                    label = stringResource(R.string.map_layer_buildings),
                    checked = layerVisibility.buildings,
                    onCheckedChange = { onLayerToggle(MapLayer.BUILDINGS, it) }
                )
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text("확인")
            }
        }
    )
}

/**
 * 레이어 토글 아이템
 */
@Composable
private fun LayerToggleItem(
    label: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(text = label)
        Switch(
            checked = checked,
            onCheckedChange = onCheckedChange
        )
    }
}
