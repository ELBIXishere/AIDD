package com.elbix.aidd.ui.adaptive

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

/**
 * 바텀시트 스캐폴드
 * - 접힌 상태에서 경로 목록 등을 표시
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AdaptiveBottomSheetScaffold(
    sheetContent: @Composable ColumnScope.() -> Unit,
    modifier: Modifier = Modifier,
    sheetPeekHeight: Int = 100,
    content: @Composable (PaddingValues) -> Unit
) {
    val bottomSheetState = rememberStandardBottomSheetState(
        initialValue = SheetValue.PartiallyExpanded
    )
    val scaffoldState = rememberBottomSheetScaffoldState(
        bottomSheetState = bottomSheetState
    )
    
    BottomSheetScaffold(
        scaffoldState = scaffoldState,
        sheetContent = {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp)
            ) {
                // 드래그 핸들
                DragHandle()
                
                sheetContent()
            }
        },
        sheetPeekHeight = sheetPeekHeight.dp,
        sheetShape = RoundedCornerShape(topStart = 16.dp, topEnd = 16.dp),
        sheetContainerColor = MaterialTheme.colorScheme.surface,
        sheetTonalElevation = 4.dp,
        modifier = modifier
    ) { paddingValues ->
        content(paddingValues)
    }
}

/**
 * 드래그 핸들 컴포넌트
 */
@Composable
private fun DragHandle() {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 12.dp),
        contentAlignment = androidx.compose.ui.Alignment.Center
    ) {
        Surface(
            modifier = Modifier
                .width(32.dp)
                .height(4.dp),
            shape = RoundedCornerShape(2.dp),
            color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.4f)
        ) {}
    }
}

/**
 * 모달 바텀시트 컴포저블
 * - 레이어 설정, 상세 정보 등에 사용
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AdaptiveModalBottomSheet(
    onDismiss: () -> Unit,
    modifier: Modifier = Modifier,
    content: @Composable ColumnScope.() -> Unit
) {
    val sheetState = rememberModalBottomSheetState()
    
    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = sheetState,
        modifier = modifier,
        shape = RoundedCornerShape(topStart = 16.dp, topEnd = 16.dp),
        containerColor = MaterialTheme.colorScheme.surface,
        tonalElevation = 4.dp
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp)
                .padding(bottom = 32.dp)
        ) {
            content()
        }
    }
}
