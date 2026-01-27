package com.elbix.aidd.ui.main.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
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

/**
 * 좌측 제어 패널 (웹 프로젝트 UI와 동일)
 * - 수용가 좌표 표시/입력
 * - 테스트 좌표 버튼
 * - 상 코드 선택 (단상/3상)
 * - 설계 실행 버튼
 * - 시설물 표시 토글
 */
@Composable
fun ControlPanel(
    modifier: Modifier = Modifier,
    coordX: String,
    coordY: String,
    phaseCode: PhaseCode,
    showFacilities: Boolean,
    layerVisibility: LayerVisibility,
    isValidInput: Boolean,
    isDesignLoading: Boolean,
    onCoordXChange: (String) -> Unit,
    onCoordYChange: (String) -> Unit,
    onPhaseCodeChange: (PhaseCode) -> Unit,
    onFacilitiesToggle: (Boolean) -> Unit,
    onLayerToggle: (MapLayer, Boolean) -> Unit,
    onRefreshFacilities: () -> Unit,
    onMoveToCoordinate: (Coordinate) -> Unit,
    onSubmitDesign: () -> Unit,
    onClearCoord: () -> Unit = {}
) {
    val scrollState = rememberScrollState()
    
    // 직접 입력 모드
    var isManualInput by remember { mutableStateOf(false) }
    var inputX by remember { mutableStateOf("") }
    var inputY by remember { mutableStateOf("") }
    
    Column(
        modifier = modifier
            .fillMaxHeight()
            .background(BgSecondary)
            .padding(16.dp)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // ===== 섹션 헤더: 설계 설정 =====
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
        
        // ===== 수용가 좌표 =====
        Text(
            text = "수용가 좌표 (EPSG:3857)",
            style = MaterialTheme.typography.labelSmall,
            color = TextSecondary
        )
        
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
                    // 헤더 행
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "선택된 좌표",
                            style = MaterialTheme.typography.labelSmall,
                            color = TextSecondary
                        )
                        TextButton(
                            onClick = onClearCoord,
                            contentPadding = PaddingValues(horizontal = 8.dp, vertical = 4.dp)
                        ) {
                            Text(
                                text = "✕ 취소",
                                style = MaterialTheme.typography.labelSmall,
                                color = Color(0xFFF87171)
                            )
                        }
                    }
                    
                    Spacer(Modifier.height(8.dp))
                    
                    // X 좌표
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(
                            text = "X:",
                            style = MaterialTheme.typography.bodySmall,
                            color = TextSecondary,
                            fontFamily = FontFamily.Monospace
                        )
                        Text(
                            text = coordX,
                            style = MaterialTheme.typography.bodySmall,
                            color = TextPrimary,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                    
                    // Y 좌표
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(
                            text = "Y:",
                            style = MaterialTheme.typography.bodySmall,
                            color = TextSecondary,
                            fontFamily = FontFamily.Monospace
                        )
                        Text(
                            text = coordY,
                            style = MaterialTheme.typography.bodySmall,
                            color = TextPrimary,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
            } else {
                // 좌표 미선택 시
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
        
        // 직접 입력 토글
        TextButton(
            onClick = { isManualInput = !isManualInput },
            contentPadding = PaddingValues(0.dp)
        ) {
            Text(
                text = if (isManualInput) "취소" else "좌표 직접 입력",
                style = MaterialTheme.typography.labelSmall,
                color = AccentColor
            )
        }
        
        // 직접 입력 폼
        if (isManualInput) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                OutlinedTextField(
                    value = inputX,
                    onValueChange = { inputX = it },
                    label = { Text("X 좌표") },
                    singleLine = true,
                    modifier = Modifier.weight(1f),
                    colors = OutlinedTextFieldDefaults.colors(
                        unfocusedBorderColor = BorderColor,
                        focusedBorderColor = AccentColor
                    )
                )
                OutlinedTextField(
                    value = inputY,
                    onValueChange = { inputY = it },
                    label = { Text("Y 좌표") },
                    singleLine = true,
                    modifier = Modifier.weight(1f),
                    colors = OutlinedTextFieldDefaults.colors(
                        unfocusedBorderColor = BorderColor,
                        focusedBorderColor = AccentColor
                    )
                )
            }
            
            Button(
                onClick = {
                    val x = inputX.toDoubleOrNull()
                    val y = inputY.toDoubleOrNull()
                    if (x != null && y != null) {
                        onCoordXChange(String.format("%.2f", x))
                        onCoordYChange(String.format("%.2f", y))
                        isManualInput = false
                    }
                },
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(
                    containerColor = BgPrimary
                )
            ) {
                Text("좌표 적용")
            }
        }
        
        // ===== 테스트 좌표 =====
        Text(
            text = "테스트 좌표",
            style = MaterialTheme.typography.labelSmall,
            color = TextSecondary
        )
        
        // 테스트 좌표 버튼들 (웹처럼 가로 나열)
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
                            // 좌표도 함께 설정
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
        
        HorizontalDivider(color = BorderColor)
        
        // ===== 신청 규격 (상 선택) =====
        Text(
            text = "신청 규격",
            style = MaterialTheme.typography.labelSmall,
            color = TextSecondary
        )
        
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // 단상 버튼
            PhaseButton(
                label = "단상",
                isSelected = phaseCode == PhaseCode.SINGLE,
                onClick = { onPhaseCodeChange(PhaseCode.SINGLE) },
                modifier = Modifier.weight(1f)
            )
            
            // 3상 버튼
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
        
        if (!isValidInput) {
            Text(
                text = "지도에서 수용가 위치를 먼저 선택하세요",
                style = MaterialTheme.typography.labelSmall,
                color = TextSecondary,
                modifier = Modifier.fillMaxWidth()
            )
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
                // 새로고침 버튼
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
                
                // 토글 스위치
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
        
        Text(
            text = "현재 화면 영역의 전주, 전선, 변압기 등을 표시합니다",
            style = MaterialTheme.typography.labelSmall,
            color = TextSecondary,
            fontSize = 11.sp
        )
        
        if (showFacilities) {
            Text(
                text = "✓ 시설물 표시 중 (지도 이동 후 새로고침)",
                style = MaterialTheme.typography.labelSmall,
                color = Color(0xFF4ADE80),
                fontSize = 11.sp
            )
        }
        
        // 하단 여백
        Spacer(Modifier.height(16.dp))
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
