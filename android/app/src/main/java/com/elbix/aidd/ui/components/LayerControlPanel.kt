package com.elbix.aidd.ui.components

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

/**
 * 레이어 컨트롤 패널
 * - 지도 레이어 가시성 토글
 */
@Composable
fun LayerControlPanel(
    modifier: Modifier = Modifier,
    layers: List<LayerItem>,
    onLayerToggle: (String, Boolean) -> Unit
) {
    Card(
        modifier = modifier,
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(
                text = "레이어 설정",
                style = MaterialTheme.typography.titleMedium
            )
            
            Divider()
            
            layers.forEach { layer ->
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = layer.name,
                        style = MaterialTheme.typography.bodyMedium
                    )
                    Switch(
                        checked = layer.isVisible,
                        onCheckedChange = { onLayerToggle(layer.id, it) }
                    )
                }
            }
        }
    }
}

/**
 * 레이어 아이템 데이터
 */
data class LayerItem(
    val id: String,
    val name: String,
    val isVisible: Boolean
)
