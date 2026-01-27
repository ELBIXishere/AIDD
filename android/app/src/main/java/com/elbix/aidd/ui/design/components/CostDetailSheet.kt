package com.elbix.aidd.ui.design.components

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.elbix.aidd.domain.model.RouteResult

/**
 * 공사비 상세 시트
 * - 경로별 비용 상세 내역 표시
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CostDetailSheet(
    route: RouteResult,
    onDismiss: () -> Unit
) {
    ModalBottomSheet(
        onDismissRequest = onDismiss
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 24.dp)
                .padding(bottom = 32.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // 헤더
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "공사비 상세",
                    style = MaterialTheme.typography.titleLarge
                )
                Surface(
                    shape = MaterialTheme.shapes.small,
                    color = MaterialTheme.colorScheme.primaryContainer
                ) {
                    Text(
                        text = "${route.rank}순위",
                        modifier = Modifier.padding(horizontal = 12.dp, vertical = 4.dp),
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.onPrimaryContainer
                    )
                }
            }
            
            Divider()
            
            // 재료비 섹션
            CostSection(
                title = "재료비",
                icon = Icons.Default.Inventory
            ) {
                CostRow(
                    label = "전주 (${route.newPolesCount}개)",
                    value = route.poleCost,
                    spec = route.poleSpec
                )
                CostRow(
                    label = "전선 (${String.format("%.1f", route.totalDistance)}m)",
                    value = route.wireCost,
                    spec = route.wireSpec
                )
            }
            
            // 인건비 섹션
            CostSection(
                title = "인건비",
                icon = Icons.Default.Engineering
            ) {
                CostRow(
                    label = "설치 노무비",
                    value = route.laborCost
                )
            }
            
            Divider()
            
            // 합계
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    text = "총 공사비",
                    style = MaterialTheme.typography.titleMedium
                )
                Text(
                    text = "${route.formattedCost}원",
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.primary
                )
            }
            
            // 전압 강하 정보
            route.voltageDrop?.let { vd ->
                Divider()
                
                VoltageDropSection(voltageDrop = vd)
            }
            
            // 비고
            route.remark?.let { remark ->
                Surface(
                    modifier = Modifier.fillMaxWidth(),
                    shape = MaterialTheme.shapes.medium,
                    color = MaterialTheme.colorScheme.surfaceVariant
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Default.Info,
                            contentDescription = null,
                            modifier = Modifier.size(20.dp),
                            tint = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Text(
                            text = remark,
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
        }
    }
}

/**
 * 비용 섹션
 */
@Composable
private fun CostSection(
    title: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    content: @Composable ColumnScope.() -> Unit
) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                modifier = Modifier.size(20.dp),
                tint = MaterialTheme.colorScheme.primary
            )
            Text(
                text = title,
                style = MaterialTheme.typography.titleSmall,
                color = MaterialTheme.colorScheme.primary
            )
        }
        
        Column(
            modifier = Modifier.padding(start = 28.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp)
        ) {
            content()
        }
    }
}

/**
 * 비용 행
 */
@Composable
private fun CostRow(
    label: String,
    value: Int,
    spec: String? = null
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Column {
            Text(
                text = label,
                style = MaterialTheme.typography.bodyMedium
            )
            spec?.let {
                Text(
                    text = "규격: $it",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
        Text(
            text = "${String.format("%,d", value)}원",
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = FontWeight.Medium
        )
    }
}

/**
 * 전압 강하 섹션
 */
@Composable
private fun VoltageDropSection(
    voltageDrop: com.elbix.aidd.domain.model.VoltageDrop
) {
    val statusColor = if (voltageDrop.isAcceptable) {
        MaterialTheme.colorScheme.primary
    } else {
        MaterialTheme.colorScheme.error
    }
    
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Icon(
                imageVector = Icons.Default.TrendingDown,
                contentDescription = null,
                modifier = Modifier.size(20.dp),
                tint = statusColor
            )
            Text(
                text = "전압 강하",
                style = MaterialTheme.typography.titleSmall,
                color = statusColor
            )
            
            Surface(
                shape = MaterialTheme.shapes.small,
                color = statusColor.copy(alpha = 0.1f)
            ) {
                Text(
                    text = if (voltageDrop.isAcceptable) "적합" else "부적합",
                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp),
                    style = MaterialTheme.typography.labelSmall,
                    color = statusColor
                )
            }
        }
        
        Column(
            modifier = Modifier.padding(start = 28.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text("전압 강하율", style = MaterialTheme.typography.bodyMedium)
                Text(
                    "${voltageDrop.formattedPercent}%",
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.Medium,
                    color = statusColor
                )
            }
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text("허용 한계", style = MaterialTheme.typography.bodyMedium)
                Text(
                    "${voltageDrop.limitPercent}%",
                    style = MaterialTheme.typography.bodyMedium
                )
            }
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text("전압 강하", style = MaterialTheme.typography.bodyMedium)
                Text(
                    "${String.format("%.2f", voltageDrop.voltageDropV)}V",
                    style = MaterialTheme.typography.bodyMedium
                )
            }
        }
    }
}
