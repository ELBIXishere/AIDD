package com.elbix.aidd.ui.main.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.elbix.aidd.domain.model.Coordinate
import com.elbix.aidd.domain.model.DesignResult
import com.elbix.aidd.domain.model.PhaseCode
import com.elbix.aidd.ui.main.LayerVisibility
import com.elbix.aidd.ui.main.MapLayer
import com.elbix.aidd.util.CoordinateUtils

// 다크 테마 색상 (웹과 유사)
private val BgPrimary = Color(0xFF0F172A)
private val BgSecondary = Color(0xFF1E293B)
private val AccentColor = Color(0xFF3B82F6)
private val TextPrimary = Color(0xFFE2E8F0)
private val TextSecondary = Color(0xFF94A3B8)
private val BorderColor = Color(0xFF334155)
private val GreenColor = Color(0xFF22C55E)
private val AmberColor = Color(0xFFF59E0B)

/**
 * 모바일 레이아웃용 바텀시트 (웹 프로젝트 스타일)
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ControlBottomSheet(
    sheetState: SheetState,
    // 좌표 입력
    coordX: String,
    coordY: String,
    phaseCode: PhaseCode,
    isValidInput: Boolean,
    onCoordXChange: (String) -> Unit,
    onCoordYChange: (String) -> Unit,
    onPhaseCodeChange: (PhaseCode) -> Unit,
    // 설계
    isDesignLoading: Boolean,
    designResult: DesignResult?,
    selectedRouteIndex: Int,
    onSubmitDesign: () -> Unit,
    onRouteSelect: (Int) -> Unit,
    onClearResult: () -> Unit,
    // 시설물
    showFacilities: Boolean,
    layerVisibility: LayerVisibility,
    onFacilitiesToggle: (Boolean) -> Unit,
    onLayerToggle: (MapLayer, Boolean) -> Unit,
    onRefreshFacilities: () -> Unit,
    // 테스트 좌표
    onMoveToCoordinate: (Coordinate) -> Unit,
    // 시트 제어
    onDismiss: () -> Unit
) {
    val scrollState = rememberScrollState()
    
    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = sheetState,
        containerColor = BgSecondary
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp)
                .padding(bottom = 32.dp)
                .verticalScroll(scrollState),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // ===== 설계 결과 (있을 때 먼저 표시) =====
            designResult?.let { result ->
                DesignResultSection(
                    result = result,
                    selectedRouteIndex = selectedRouteIndex,
                    onRouteSelect = onRouteSelect,
                    onClear = onClearResult
                )
                
                HorizontalDivider(color = BorderColor)
            }
            
            // ===== 좌표 입력 섹션 =====
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Icon(
                    Icons.Default.Settings,
                    contentDescription = null,
                    tint = AccentColor,
                    modifier = Modifier.size(16.dp)
                )
                Text(
                    text = "설계 설정",
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.SemiBold,
                    color = TextPrimary
                )
            }
            
            // 좌표 표시 박스
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(8.dp))
                    .background(BgPrimary)
                    .padding(12.dp)
            ) {
                if (coordX.isNotEmpty() && coordY.isNotEmpty()) {
                    Column {
                        Text(
                            text = "선택된 좌표",
                            style = MaterialTheme.typography.labelSmall,
                            color = TextSecondary
                        )
                        Spacer(Modifier.height(4.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text("X:", color = TextSecondary, fontFamily = FontFamily.Monospace, fontSize = 12.sp)
                            Text(coordX, color = TextPrimary, fontFamily = FontFamily.Monospace, fontSize = 12.sp)
                        }
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text("Y:", color = TextSecondary, fontFamily = FontFamily.Monospace, fontSize = 12.sp)
                            Text(coordY, color = TextPrimary, fontFamily = FontFamily.Monospace, fontSize = 12.sp)
                        }
                    }
                } else {
                    Text(
                        text = "지도를 클릭하여 위치 선택",
                        style = MaterialTheme.typography.bodySmall,
                        color = TextSecondary,
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 8.dp)
                    )
                }
            }
            
            // ===== 테스트 좌표 버튼 =====
            Text(
                text = "테스트 좌표",
                style = MaterialTheme.typography.labelSmall,
                color = TextSecondary
            )
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(4.dp)
            ) {
                CoordinateUtils.TestCoordinates.ALL.forEach { (name, coord) ->
                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .clip(RoundedCornerShape(4.dp))
                            .background(BgPrimary)
                            .clickable {
                                onMoveToCoordinate(coord)
                                onCoordXChange(String.format("%.2f", coord.x))
                                onCoordYChange(String.format("%.2f", coord.y))
                            }
                            .padding(horizontal = 4.dp, vertical = 8.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = name,
                            style = MaterialTheme.typography.labelSmall,
                            color = TextSecondary,
                            fontSize = 10.sp
                        )
                    }
                }
            }
            
            // ===== 상 코드 선택 =====
            Text(
                text = "신청 규격",
                style = MaterialTheme.typography.labelSmall,
                color = TextSecondary
            )
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                PhaseButton(
                    label = "단상",
                    isSelected = phaseCode == PhaseCode.SINGLE,
                    onClick = { onPhaseCodeChange(PhaseCode.SINGLE) },
                    modifier = Modifier.weight(1f)
                )
                PhaseButton(
                    label = "3상",
                    isSelected = phaseCode == PhaseCode.THREE,
                    onClick = { onPhaseCodeChange(PhaseCode.THREE) },
                    modifier = Modifier.weight(1f)
                )
            }
            
            // ===== 설계 실행 버튼 =====
            Button(
                onClick = onSubmitDesign,
                enabled = isValidInput && !isDesignLoading,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(48.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = AccentColor,
                    disabledContainerColor = AccentColor.copy(alpha = 0.5f)
                ),
                shape = RoundedCornerShape(8.dp)
            ) {
                if (isDesignLoading) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(20.dp),
                        strokeWidth = 2.dp,
                        color = Color.White
                    )
                    Spacer(Modifier.width(8.dp))
                    Text("설계 분석 중...", color = Color.White)
                } else {
                    Icon(Icons.Default.PlayArrow, contentDescription = null, tint = Color.White)
                    Spacer(Modifier.width(8.dp))
                    Text("설계 실행", color = Color.White, fontWeight = FontWeight.Medium)
                }
            }
            
            HorizontalDivider(color = BorderColor)
            
            // ===== 시설물 표시 =====
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "시설물 표시",
                    style = MaterialTheme.typography.labelSmall,
                    color = TextSecondary
                )
                
                Row(
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    if (showFacilities) {
                        IconButton(
                            onClick = onRefreshFacilities,
                            modifier = Modifier.size(24.dp)
                        ) {
                            Icon(
                                Icons.Default.Refresh,
                                contentDescription = "새로고침",
                                tint = TextSecondary,
                                modifier = Modifier.size(16.dp)
                            )
                        }
                    }
                    
                    Switch(
                        checked = showFacilities,
                        onCheckedChange = onFacilitiesToggle,
                        colors = SwitchDefaults.colors(
                            checkedTrackColor = AccentColor,
                            uncheckedTrackColor = BorderColor
                        )
                    )
                }
            }
            
            if (showFacilities) {
                Text(
                    text = "✓ 시설물 표시 중",
                    style = MaterialTheme.typography.labelSmall,
                    color = GreenColor,
                    fontSize = 11.sp
                )
            }
        }
    }
}

/**
 * 상(Phase) 선택 버튼
 */
@Composable
private fun PhaseButton(
    label: String,
    isSelected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val backgroundColor = if (isSelected) AccentColor.copy(alpha = 0.2f) else BgPrimary
    val borderColor = if (isSelected) AccentColor else BorderColor
    val textColor = if (isSelected) AccentColor else TextSecondary
    
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(8.dp))
            .background(backgroundColor)
            .border(2.dp, borderColor, RoundedCornerShape(8.dp))
            .clickable(onClick = onClick)
            .padding(vertical = 12.dp),
        contentAlignment = Alignment.Center
    ) {
        Row(
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                Icons.Default.Bolt,
                contentDescription = null,
                tint = textColor,
                modifier = Modifier.size(20.dp)
            )
            Text(
                text = label,
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.Medium,
                color = textColor
            )
        }
    }
}

/**
 * 설계 결과 섹션 (바텀시트 내)
 */
@Composable
private fun DesignResultSection(
    result: DesignResult,
    selectedRouteIndex: Int,
    onRouteSelect: (Int) -> Unit,
    onClear: () -> Unit
) {
    Column(
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(
                    Icons.Default.Check,
                    contentDescription = null,
                    tint = GreenColor,
                    modifier = Modifier.size(16.dp)
                )
                Text(
                    text = "설계 결과",
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.SemiBold,
                    color = TextPrimary
                )
            }
            TextButton(onClick = onClear) {
                Text("초기화", color = AccentColor, fontSize = 12.sp)
            }
        }
        
        if (result.routes.isEmpty()) {
            Text(
                text = "설계 가능한 경로가 없습니다",
                color = AmberColor,
                fontSize = 12.sp
            )
        } else {
            Text(
                text = "경로 ${result.routes.size}개 발견",
                style = MaterialTheme.typography.labelSmall,
                color = TextSecondary
            )
            
            // 경로 선택 버튼
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                result.routes.take(3).forEachIndexed { index, route ->
                    val isSelected = index == selectedRouteIndex
                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .clip(RoundedCornerShape(8.dp))
                            .background(if (isSelected) AccentColor.copy(alpha = 0.2f) else BgPrimary)
                            .border(
                                if (isSelected) 2.dp else 1.dp,
                                if (isSelected) AccentColor else BorderColor,
                                RoundedCornerShape(8.dp)
                            )
                            .clickable { onRouteSelect(index) }
                            .padding(8.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Column(
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            Text(
                                text = if (index == 0) "최적" else "경로${index + 1}",
                                style = MaterialTheme.typography.labelSmall,
                                color = if (isSelected) AccentColor else TextSecondary,
                                fontSize = 10.sp
                            )
                            Text(
                                text = "${route.formattedCost}원",
                                style = MaterialTheme.typography.labelSmall,
                                color = TextPrimary,
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Medium
                            )
                        }
                    }
                }
            }
            
            // 선택된 경로 요약
            result.routes.getOrNull(selectedRouteIndex)?.let { route ->
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(8.dp))
                        .background(BgPrimary)
                        .padding(12.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text(
                            text = "전주 ${route.newPolesCount}개 · ${route.formattedDistance}m",
                            style = MaterialTheme.typography.labelSmall,
                            color = TextSecondary
                        )
                    }
                    Text(
                        text = "총 ${route.formattedCost}원",
                        style = MaterialTheme.typography.titleSmall,
                        fontWeight = FontWeight.Bold,
                        color = AccentColor
                    )
                }
            }
        }
    }
}
