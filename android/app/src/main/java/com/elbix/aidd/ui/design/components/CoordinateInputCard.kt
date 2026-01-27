package com.elbix.aidd.ui.design.components

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp

/**
 * 좌표 입력 카드
 * - X, Y 좌표 입력 필드
 * - EPSG:3857 좌표계
 */
@Composable
fun CoordinateInputCard(
    coordX: String,
    coordY: String,
    onCoordXChange: (String) -> Unit,
    onCoordYChange: (String) -> Unit,
    modifier: Modifier = Modifier,
    isExpanded: Boolean = false
) {
    Card(
        modifier = modifier.fillMaxWidth()
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // 헤더
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Icon(
                    imageVector = Icons.Default.LocationOn,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary
                )
                Text(
                    text = "수용가 위치",
                    style = MaterialTheme.typography.titleMedium
                )
            }
            
            Text(
                text = "좌표계: EPSG:3857 (Web Mercator)",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            
            // 좌표 입력 필드
            if (isExpanded) {
                // 펼친 상태: 가로 배치
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    CoordinateTextField(
                        value = coordX,
                        onValueChange = onCoordXChange,
                        label = "X 좌표",
                        placeholder = "14241940.81",
                        modifier = Modifier.weight(1f)
                    )
                    
                    CoordinateTextField(
                        value = coordY,
                        onValueChange = onCoordYChange,
                        label = "Y 좌표",
                        placeholder = "4437601.67",
                        modifier = Modifier.weight(1f)
                    )
                }
            } else {
                // 접은 상태: 세로 배치
                CoordinateTextField(
                    value = coordX,
                    onValueChange = onCoordXChange,
                    label = "X 좌표",
                    placeholder = "14241940.81",
                    modifier = Modifier.fillMaxWidth()
                )
                
                CoordinateTextField(
                    value = coordY,
                    onValueChange = onCoordYChange,
                    label = "Y 좌표",
                    placeholder = "4437601.67",
                    modifier = Modifier.fillMaxWidth()
                )
            }
        }
    }
}

/**
 * 좌표 입력 텍스트 필드
 */
@Composable
private fun CoordinateTextField(
    value: String,
    onValueChange: (String) -> Unit,
    label: String,
    placeholder: String,
    modifier: Modifier = Modifier
) {
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        label = { Text(label) },
        placeholder = { Text(placeholder) },
        modifier = modifier,
        singleLine = true,
        keyboardOptions = KeyboardOptions(
            keyboardType = KeyboardType.Decimal
        ),
        supportingText = {
            // 입력 유효성 표시
            if (value.isNotEmpty() && value.toDoubleOrNull() == null) {
                Text(
                    text = "숫자를 입력하세요",
                    color = MaterialTheme.colorScheme.error
                )
            }
        },
        isError = value.isNotEmpty() && value.toDoubleOrNull() == null
    )
}
