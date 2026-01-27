package com.elbix.aidd.ui.navigation

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Build
import androidx.compose.material.icons.filled.List
import androidx.compose.material.icons.filled.Map
import androidx.compose.material.icons.filled.Settings
import androidx.compose.ui.graphics.vector.ImageVector
import com.elbix.aidd.R

/**
 * 화면 라우트 정의
 */
sealed class Screen(val route: String) {
    object Map : Screen("map")
    object Design : Screen("design")
    object Facilities : Screen("facilities")
    object Settings : Screen("settings")
}

/**
 * 하단 네비게이션 아이템 정의
 */
sealed class BottomNavItem(
    val screen: Screen,
    val icon: ImageVector,
    val titleResId: Int
) {
    object Map : BottomNavItem(
        screen = Screen.Map,
        icon = Icons.Default.Map,
        titleResId = R.string.menu_map
    )
    
    object Design : BottomNavItem(
        screen = Screen.Design,
        icon = Icons.Default.Build,
        titleResId = R.string.menu_design
    )
    
    object Facilities : BottomNavItem(
        screen = Screen.Facilities,
        icon = Icons.Default.List,
        titleResId = R.string.menu_facilities
    )
    
    object Settings : BottomNavItem(
        screen = Screen.Settings,
        icon = Icons.Default.Settings,
        titleResId = R.string.menu_settings
    )
}
