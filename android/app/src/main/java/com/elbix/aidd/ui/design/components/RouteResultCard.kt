package com.elbix.aidd.ui.design.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.elbix.aidd.domain.model.RouteResult
import com.elbix.aidd.ui.theme.*

/**
 * 경로 결과 카드
 * - 개별 경로 정보 표시
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RouteResultCard(
    route: RouteResult,
    isSelected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val rankColor = getRankColor(route.rank)
    val borderColor = if (isSelected) rankColor else Color.Transparent
    
    Card(
        onClick = onClick,
        modifier = modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = if (isSelected) {
                rankColor.copy(alpha = 0.1f)
            } else {
                MaterialTheme.colorScheme.surface
            }
        ),
        border = BorderStroke(
            width = if (isSelected) 2.dp else 0.dp,
            color = borderColor
        ),
        elevation = CardDefaults.cardElevation(
            defaultElevation = if (isSelected) 4.dp else 1.dp
        )
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // 헤더 (순위 + 공사비)
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                // 순위 배지
                Surface(
                    shape = MaterialTheme.shapes.small,
                    color = rankColor
                ) {
                    Text(
                        text = "${route.rank}순위",
                        modifier = Modifier.padding(horizontal = 12.dp, vertical = 4.dp),
                        style = MaterialTheme.typography.labelMedium,
                        color = Color.White
                    )
                }
                
                // 공사비
                Text(
                    text = "${route.formattedCost}원",
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold,
                    color = rankColor
                )
            }
            
            Divider()
            
            // 상세 정보
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                // 거리
                InfoColumn(
                    icon = Icons.Default.Straighten,
                    label = "거리",
                    value = "${route.formattedDistance}m"
                )
                
                // 신설 전주
                InfoColumn(
                    icon = Icons.Default.ElectricBolt,
                    label = "신설 전주",
                    value = "${route.newPolesCount}개"
                )
                
                // 전압 강하
                route.voltageDrop?.let { vd ->
                    InfoColumn(
                        icon = Icons.Default.TrendingDown,
                        label = "전압 강하",
                        value = "${vd.formattedPercent}%",
                        isWarning = !vd.isAcceptable
                    )
                }
            }
            
            // Fast Track 표시
            if (route.isFastTrack) {
                Surface(
                    shape = MaterialTheme.shapes.small,
                    color = Success.copy(alpha = 0.1f)
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                        horizontalArrangement = Arrangement.spacedBy(4.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            imageVector = Icons.Default.Bolt,
                            contentDescription = null,
                            modifier = Modifier.size(16.dp),
                            tint = Success
                        )
                        Text(
                            text = "Fast Track",
                            style = MaterialTheme.typography.labelSmall,
                            color = Success
                        )
                    }
                }
            }
            
            // 비고
            route.remark?.let { remark ->
                if (!route.isFastTrack) {
                    Text(
                        text = remark,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        }
    }
}

/**
 * 정보 컬럼
 */
@Composable
private fun InfoColumn(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    label: String,
    value: String,
    isWarning: Boolean = false
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Icon(
            imageVector = icon,
            contentDescription = null,
            modifier = Modifier.size(20.dp),
            tint = if (isWarning) Error else MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(modifier = Modifier.height(4.dp))
        Text(
            text = label,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Text(
            text = value,
            style = MaterialTheme.typography.titleSmall,
            fontWeight = FontWeight.Medium,
            color = if (isWarning) Error else MaterialTheme.colorScheme.onSurface
        )
    }
}

/**
 * 순위별 색상 반환
 */
private fun getRankColor(rank: Int): Color {
    return when (rank) {
        1 -> Route1
        2 -> Route2
        3 -> Route3
        4 -> Route4
        else -> Route5
    }
}
