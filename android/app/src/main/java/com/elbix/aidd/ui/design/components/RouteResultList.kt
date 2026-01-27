package com.elbix.aidd.ui.design.components

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.elbix.aidd.domain.model.RouteResult

/**
 * 경로 결과 목록
 * - 설계 결과의 모든 경로 표시
 */
@Composable
fun RouteResultList(
    routes: List<RouteResult>,
    selectedIndex: Int,
    onRouteSelect: (Int) -> Unit,
    modifier: Modifier = Modifier
) {
    if (routes.isEmpty()) {
        // 빈 상태
        EmptyRouteState(modifier = modifier)
    } else {
        LazyColumn(
            modifier = modifier,
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // 요약 헤더
            item {
                RouteListHeader(
                    totalRoutes = routes.size,
                    bestCost = routes.firstOrNull()?.formattedCost ?: "0"
                )
            }
            
            // 경로 목록
            itemsIndexed(routes) { index, route ->
                RouteResultCard(
                    route = route,
                    isSelected = index == selectedIndex,
                    onClick = { onRouteSelect(index) }
                )
            }
            
            // 하단 여백
            item {
                Spacer(modifier = Modifier.height(16.dp))
            }
        }
    }
}

/**
 * 경로 목록 헤더
 */
@Composable
private fun RouteListHeader(
    totalRoutes: Int,
    bestCost: String
) {
    Card(
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.primaryContainer
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            Text(
                text = "설계 완료",
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onPrimaryContainer
            )
            Spacer(modifier = Modifier.height(8.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Column {
                    Text(
                        text = "발견된 경로",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f)
                    )
                    Text(
                        text = "${totalRoutes}개",
                        style = MaterialTheme.typography.titleLarge,
                        color = MaterialTheme.colorScheme.onPrimaryContainer
                    )
                }
                Column(horizontalAlignment = Alignment.End) {
                    Text(
                        text = "최저 공사비",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f)
                    )
                    Text(
                        text = "${bestCost}원",
                        style = MaterialTheme.typography.titleLarge,
                        color = MaterialTheme.colorScheme.onPrimaryContainer
                    )
                }
            }
        }
    }
}

/**
 * 빈 상태 표시
 */
@Composable
private fun EmptyRouteState(
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(
                text = "😕",
                style = MaterialTheme.typography.displayMedium
            )
            Text(
                text = "경로를 찾을 수 없습니다",
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Text(
                text = "조건을 변경하여 다시 시도해주세요",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                textAlign = TextAlign.Center
            )
        }
    }
}
