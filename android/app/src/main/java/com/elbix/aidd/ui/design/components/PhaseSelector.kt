package com.elbix.aidd.ui.design.components

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ElectricalServices
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.elbix.aidd.R
import com.elbix.aidd.domain.model.PhaseCode

/**
 * 상(Phase) 선택 컴포넌트
 * - 단상 / 3상 선택
 */
@Composable
fun PhaseSelector(
    selectedPhase: PhaseCode,
    onPhaseSelect: (PhaseCode) -> Unit,
    modifier: Modifier = Modifier
) {
    Card(modifier = modifier.fillMaxWidth()) {
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
                    imageVector = Icons.Default.ElectricalServices,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary
                )
                Text(
                    text = "신청 규격",
                    style = MaterialTheme.typography.titleMedium
                )
            }
            
            // 선택 버튼 그룹
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                PhaseOption.entries.forEach { option ->
                    PhaseButton(
                        option = option,
                        isSelected = selectedPhase == option.phaseCode,
                        onClick = { onPhaseSelect(option.phaseCode) },
                        modifier = Modifier.weight(1f)
                    )
                }
            }
        }
    }
}

/**
 * 상 옵션 버튼
 */
@Composable
private fun PhaseButton(
    option: PhaseOption,
    isSelected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val containerColor = if (isSelected) {
        MaterialTheme.colorScheme.primaryContainer
    } else {
        MaterialTheme.colorScheme.surfaceVariant
    }
    
    val contentColor = if (isSelected) {
        MaterialTheme.colorScheme.onPrimaryContainer
    } else {
        MaterialTheme.colorScheme.onSurfaceVariant
    }
    
    Surface(
        onClick = onClick,
        modifier = modifier.height(80.dp),
        shape = MaterialTheme.shapes.medium,
        color = containerColor,
        contentColor = contentColor,
        tonalElevation = if (isSelected) 4.dp else 0.dp
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(12.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text(
                text = option.displayName,
                style = MaterialTheme.typography.titleMedium
            )
            Text(
                text = option.description,
                style = MaterialTheme.typography.bodySmall
            )
        }
    }
}

/**
 * 상 옵션 열거형
 */
private enum class PhaseOption(
    val phaseCode: PhaseCode,
    val displayName: String,
    val description: String
) {
    SINGLE(PhaseCode.SINGLE, "단상", "일반 가정용"),
    THREE(PhaseCode.THREE, "3상", "산업/상업용")
}
