package com.elbix.aidd.ui.main.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
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
import com.elbix.aidd.domain.model.DesignResult
import com.elbix.aidd.domain.model.RouteResult

// 다크 테마 색상 (웹과 유사)
private val BgPrimary = Color(0xFF0F172A)
private val BgSecondary = Color(0xFF1E293B)
private val AccentColor = Color(0xFF3B82F6)
private val TextPrimary = Color(0xFFE2E8F0)
private val TextSecondary = Color(0xFF94A3B8)
private val BorderColor = Color(0xFF334155)
private val GreenColor = Color(0xFF22C55E)
private val AmberColor = Color(0xFFF59E0B)
private val RedColor = Color(0xFFEF4444)

/**
 * 우측 결과 패널 (웹 프로젝트 UI와 동일)
 * - 경로 목록 (카드 형태)
 * - 신설 전주/거리/비용지수/예상비용 2x2 그리드
 * - 기설 전주 정보
 * - 전압강하 정보
 * - 비용 상세 (선택 시)
 */
@Composable
fun ResultPanel(
    modifier: Modifier = Modifier,
    result: DesignResult,
    selectedRouteIndex: Int,
    onRouteSelect: (Int) -> Unit,
    onClose: () -> Unit
) {
    Column(
        modifier = modifier
            .fillMaxHeight()
            .background(BgSecondary)
    ) {
        // ===== 헤더 =====
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
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
                
                Row(
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "${result.routes.size}개 경로",
                        style = MaterialTheme.typography.labelSmall,
                        color = TextSecondary
                    )
                    IconButton(
                        onClick = onClose,
                        modifier = Modifier.size(24.dp)
                    ) {
                        Icon(
                            Icons.Default.Close,
                            contentDescription = "닫기",
                            tint = TextSecondary,
                            modifier = Modifier.size(16.dp)
                        )
                    }
                }
            }
            
            // 요청 규격 배지
            Row(
                modifier = Modifier.padding(top = 8.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                // 상 배지
                val isThreePhase = result.requestSpec.contains("3상")
                Badge(
                    text = result.requestSpec,
                    backgroundColor = if (isThreePhase) AmberColor.copy(alpha = 0.2f) else AccentColor.copy(alpha = 0.2f),
                    textColor = if (isThreePhase) AmberColor else AccentColor,
                    borderColor = if (isThreePhase) AmberColor.copy(alpha = 0.3f) else AccentColor.copy(alpha = 0.3f)
                )
                
                // 전압 배지
                Badge(
                    text = if (isThreePhase) "고압" else "저압",
                    backgroundColor = if (isThreePhase) RedColor.copy(alpha = 0.2f) else GreenColor.copy(alpha = 0.2f),
                    textColor = if (isThreePhase) RedColor else GreenColor,
                    borderColor = if (isThreePhase) RedColor.copy(alpha = 0.3f) else GreenColor.copy(alpha = 0.3f)
                )
            }
            
            // 처리 시간
            result.processingTimeMs?.let { time ->
                Text(
                    text = "처리 시간: ${time}ms",
                    style = MaterialTheme.typography.labelSmall,
                    color = TextSecondary,
                    modifier = Modifier.padding(top = 8.dp)
                )
            }
        }
        
        HorizontalDivider(color = BorderColor)
        
        // ===== 경로 목록 =====
        if (result.routes.isEmpty()) {
            // 경로 없음
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
                    .padding(16.dp),
                contentAlignment = Alignment.Center
            ) {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(8.dp))
                        .background(AmberColor.copy(alpha = 0.1f))
                        .border(1.dp, AmberColor.copy(alpha = 0.3f), RoundedCornerShape(8.dp))
                        .padding(16.dp)
                ) {
                    Icon(
                        Icons.Default.Warning,
                        contentDescription = null,
                        tint = AmberColor,
                        modifier = Modifier.size(24.dp)
                    )
                    Spacer(Modifier.height(8.dp))
                    Text(
                        text = "경로 없음",
                        style = MaterialTheme.typography.titleSmall,
                        fontWeight = FontWeight.Medium,
                        color = AmberColor
                    )
                    Text(
                        text = "조건에 맞는 경로를 찾을 수 없습니다.",
                        style = MaterialTheme.typography.bodySmall,
                        color = AmberColor.copy(alpha = 0.8f)
                    )
                }
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
                    .padding(8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                itemsIndexed(result.routes) { index, route ->
                    RouteCard(
                        route = route,
                        index = index,
                        isSelected = index == selectedRouteIndex,
                        onClick = { onRouteSelect(index) }
                    )
                }
            }
        }
    }
}

/**
 * 배지 컴포넌트
 */
@Composable
private fun Badge(
    text: String,
    backgroundColor: Color,
    textColor: Color,
    borderColor: Color
) {
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(4.dp))
            .background(backgroundColor)
            .border(1.dp, borderColor, RoundedCornerShape(4.dp))
            .padding(horizontal = 8.dp, vertical = 2.dp)
    ) {
        Text(
            text = text,
            style = MaterialTheme.typography.labelSmall,
            fontWeight = FontWeight.Medium,
            color = textColor,
            fontSize = 11.sp
        )
    }
}

/**
 * 경로 카드 컴포넌트 (웹 프로젝트와 동일한 레이아웃)
 */
@Composable
private fun RouteCard(
    route: RouteResult,
    index: Int,
    isSelected: Boolean,
    onClick: () -> Unit
) {
    val backgroundColor = if (isSelected) AccentColor.copy(alpha = 0.2f) else BgPrimary
    val borderColor = if (isSelected) AccentColor else Color.Transparent
    
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(8.dp))
            .background(backgroundColor)
            .border(2.dp, borderColor, RoundedCornerShape(8.dp))
            .clickable(onClick = onClick)
            .padding(12.dp)
    ) {
        // 헤더: 순위 + 경로 이름 + 선택 체크
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                // 순위 배지
                Box(
                    modifier = Modifier
                        .size(24.dp)
                        .clip(CircleShape)
                        .background(if (index == 0) GreenColor else BorderColor),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "${route.rank}",
                        style = MaterialTheme.typography.labelSmall,
                        fontWeight = FontWeight.Bold,
                        color = if (index == 0) Color.White else TextSecondary
                    )
                }
                
                Text(
                    text = if (index == 0) "최적 경로" else "경로 ${index + 1}",
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.Medium,
                    color = TextPrimary
                )
            }
            
            if (isSelected) {
                Icon(
                    Icons.Default.Check,
                    contentDescription = null,
                    tint = AccentColor,
                    modifier = Modifier.size(16.dp)
                )
            }
        }
        
        Spacer(Modifier.height(12.dp))
        
        // 2x2 그리드: 신설 전주, 총 거리, 비용 지수, 예상 비용
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            InfoBox(
                label = "신설 전주",
                value = "${route.newPolesCount}개",
                modifier = Modifier.weight(1f)
            )
            InfoBox(
                label = "총 거리",
                value = "${route.formattedDistance}m",
                modifier = Modifier.weight(1f)
            )
        }
        
        Spacer(Modifier.height(8.dp))
        
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            InfoBox(
                label = "비용 지수",
                value = String.format("%,d", route.costIndex),
                modifier = Modifier.weight(1f)
            )
            InfoBox(
                label = "예상 비용",
                value = route.formattedCost + "원",
                modifier = Modifier.weight(1f),
                valueSize = 11.sp
            )
        }
        
        // 기설 전주 정보
        if (route.startPoleId.isNotEmpty()) {
            Spacer(Modifier.height(8.dp))
            
            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "기설전주:",
                    style = MaterialTheme.typography.labelSmall,
                    color = TextSecondary
                )
                Text(
                    text = route.startPoleId,
                    style = MaterialTheme.typography.labelSmall,
                    color = TextSecondary,
                    fontFamily = FontFamily.Monospace
                )
                
                // 전압 유형 배지
                route.sourceVoltageType?.let { voltageType ->
                    Badge(
                        text = if (voltageType == "HV") "고압" else "저압",
                        backgroundColor = if (voltageType == "HV") RedColor.copy(alpha = 0.2f) else GreenColor.copy(alpha = 0.2f),
                        textColor = if (voltageType == "HV") RedColor else GreenColor,
                        borderColor = Color.Transparent
                    )
                }
                
                // 상 유형 배지
                route.sourcePhaseType?.let { phaseType ->
                    Badge(
                        text = if (phaseType == "3") "3상" else "단상",
                        backgroundColor = if (phaseType == "3") AmberColor.copy(alpha = 0.2f) else AccentColor.copy(alpha = 0.2f),
                        textColor = if (phaseType == "3") AmberColor else AccentColor,
                        borderColor = Color.Transparent
                    )
                }
            }
        }
        
        // 전압 강하 정보
        route.voltageDrop?.let { vd ->
            Spacer(Modifier.height(8.dp))
            
            val vdColor = if (vd.isAcceptable) GreenColor else RedColor
            val vdBgColor = if (vd.isAcceptable) GreenColor.copy(alpha = 0.1f) else RedColor.copy(alpha = 0.1f)
            
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(4.dp))
                    .background(vdBgColor)
                    .padding(horizontal = 8.dp, vertical = 4.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(
                    Icons.Default.Bolt,
                    contentDescription = null,
                    tint = vdColor,
                    modifier = Modifier.size(12.dp)
                )
                Text(
                    text = "전압강하: ${vd.formattedPercent}%" + if (!vd.isAcceptable) " (초과!)" else "",
                    style = MaterialTheme.typography.labelSmall,
                    color = vdColor
                )
            }
        }
        
        // 비용 상세 (선택 시에만)
        if (isSelected && (route.poleCost > 0 || route.wireCost > 0 || route.laborCost > 0)) {
            Spacer(Modifier.height(12.dp))
            HorizontalDivider(color = BorderColor)
            Spacer(Modifier.height(12.dp))
            
            Text(
                text = "비용 상세",
                style = MaterialTheme.typography.labelSmall,
                color = TextSecondary
            )
            
            Spacer(Modifier.height(8.dp))
            
            if (route.poleCost > 0) {
                CostRow(label = "전주 비용", value = route.poleCost)
            }
            if (route.wireCost > 0) {
                CostRow(label = "전선 비용", value = route.wireCost)
            }
            if (route.laborCost > 0) {
                CostRow(label = "인건비", value = route.laborCost)
            }
        }
    }
}

/**
 * 정보 박스 (2x2 그리드용)
 */
@Composable
private fun InfoBox(
    label: String,
    value: String,
    modifier: Modifier = Modifier,
    valueSize: androidx.compose.ui.unit.TextUnit = 14.sp
) {
    Column(
        modifier = modifier
            .clip(RoundedCornerShape(4.dp))
            .background(BgSecondary)
            .padding(8.dp)
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = TextSecondary,
            fontSize = 10.sp
        )
        Text(
            text = value,
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = FontWeight.Medium,
            color = TextPrimary,
            fontSize = valueSize
        )
    }
}

/**
 * 비용 행
 */
@Composable
private fun CostRow(
    label: String,
    value: Int
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 2.dp),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = TextSecondary
        )
        Text(
            text = String.format("%,d원", value),
            style = MaterialTheme.typography.labelSmall,
            color = TextPrimary
        )
    }
}
