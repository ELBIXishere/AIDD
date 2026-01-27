package com.elbix.aidd.ui.settings

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.elbix.aidd.BuildConfig

/**
 * 설정 화면
 * - 앱 설정 관리
 * - 서버 연결 설정
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen() {
    var serverUrl by remember { mutableStateOf(BuildConfig.API_BASE_URL) }
    var showServerDialog by remember { mutableStateOf(false) }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("설정") }
            )
        }
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // 서버 설정 섹션
            Text(
                text = "서버 설정",
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.padding(vertical = 8.dp)
            )
            
            // 서버 URL 설정
            SettingsItem(
                icon = Icons.Default.Cloud,
                title = "API 서버",
                subtitle = serverUrl,
                onClick = { showServerDialog = true }
            )
            
            Divider(modifier = Modifier.padding(vertical = 8.dp))
            
            // 지도 설정 섹션
            Text(
                text = "지도 설정",
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.padding(vertical = 8.dp)
            )
            
            SettingsItem(
                icon = Icons.Default.Map,
                title = "기본 지도 스타일",
                subtitle = "OpenStreetMap"
            )
            
            SettingsItem(
                icon = Icons.Default.MyLocation,
                title = "기본 위치",
                subtitle = "서울"
            )
            
            Divider(modifier = Modifier.padding(vertical = 8.dp))
            
            // 앱 정보 섹션
            Text(
                text = "앱 정보",
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.padding(vertical = 8.dp)
            )
            
            SettingsItem(
                icon = Icons.Default.Info,
                title = "버전",
                subtitle = "1.0.0 (${BuildConfig.VERSION_CODE})"
            )
            
            SettingsItem(
                icon = Icons.Default.Description,
                title = "ELBIX AIDD",
                subtitle = "AI 기반 배전 설계 자동화 시스템"
            )
        }
    }
    
    // 서버 URL 편집 다이얼로그
    if (showServerDialog) {
        var editedUrl by remember { mutableStateOf(serverUrl) }
        
        AlertDialog(
            onDismissRequest = { showServerDialog = false },
            title = { Text("API 서버 설정") },
            text = {
                OutlinedTextField(
                    value = editedUrl,
                    onValueChange = { editedUrl = it },
                    label = { Text("서버 URL") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        serverUrl = editedUrl
                        showServerDialog = false
                    }
                ) {
                    Text("저장")
                }
            },
            dismissButton = {
                TextButton(onClick = { showServerDialog = false }) {
                    Text("취소")
                }
            }
        )
    }
}

/**
 * 설정 아이템
 */
@Composable
private fun SettingsItem(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    title: String,
    subtitle: String,
    onClick: (() -> Unit)? = null
) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        onClick = onClick ?: {},
        enabled = onClick != null
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.primary,
                modifier = Modifier.size(24.dp)
            )
            
            Spacer(modifier = Modifier.width(16.dp))
            
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = title,
                    style = MaterialTheme.typography.bodyLarge
                )
                Text(
                    text = subtitle,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            
            if (onClick != null) {
                Icon(
                    imageVector = Icons.Default.ChevronRight,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}
