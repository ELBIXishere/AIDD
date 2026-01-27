package com.elbix.aidd.ui.theme

import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext

/**
 * ELBIX AIDD 색상 정의
 * - 전력/배전 관련 파란색 테마
 */
// 메인 색상
val Primary = Color(0xFF1976D2)
val PrimaryDark = Color(0xFF1565C0)
val PrimaryLight = Color(0xFF42A5F5)
val Secondary = Color(0xFFFF9800)
val SecondaryDark = Color(0xFFE65100)

// 상태 색상
val Success = Color(0xFF4CAF50)
val Warning = Color(0xFFFF9800)
val Error = Color(0xFFF44336)
val Info = Color(0xFF2196F3)

// 경로 색상
val Route1 = Color(0xFF4CAF50)  // 1순위: 초록
val Route2 = Color(0xFF2196F3)  // 2순위: 파랑
val Route3 = Color(0xFFFF9800)  // 3순위: 주황
val Route4 = Color(0xFF9C27B0)  // 4순위: 보라
val Route5 = Color(0xFF607D8B)  // 5순위: 회색

// 시설물 색상
val PoleExisting = Color(0xFF1976D2)  // 기설 전주
val PoleNew = Color(0xFF4CAF50)       // 신설 전주
val LineHV = Color(0xFFF44336)        // 고압선
val LineLV = Color(0xFF2196F3)        // 저압선
val Transformer = Color(0xFFFF9800)   // 변압기
val Consumer = Color(0xFFE91E63)      // 수용가

// 라이트 테마 색상 스킴
private val LightColorScheme = lightColorScheme(
    primary = Primary,
    onPrimary = Color.White,
    primaryContainer = PrimaryLight,
    onPrimaryContainer = Color.White,
    secondary = Secondary,
    onSecondary = Color.White,
    secondaryContainer = Color(0xFFFFE0B2),
    onSecondaryContainer = SecondaryDark,
    error = Error,
    onError = Color.White,
    background = Color(0xFFFAFAFA),
    onBackground = Color(0xFF1C1B1F),
    surface = Color.White,
    onSurface = Color(0xFF1C1B1F),
    surfaceVariant = Color(0xFFF5F5F5),
    onSurfaceVariant = Color(0xFF49454F),
    outline = Color(0xFF79747E)
)

// 다크 테마 색상 스킴
private val DarkColorScheme = darkColorScheme(
    primary = PrimaryLight,
    onPrimary = Color.Black,
    primaryContainer = PrimaryDark,
    onPrimaryContainer = Color.White,
    secondary = Color(0xFFFFB74D),
    onSecondary = Color.Black,
    secondaryContainer = SecondaryDark,
    onSecondaryContainer = Color.White,
    error = Color(0xFFCF6679),
    onError = Color.Black,
    background = Color(0xFF121212),
    onBackground = Color(0xFFE6E1E5),
    surface = Color(0xFF1E1E1E),
    onSurface = Color(0xFFE6E1E5),
    surfaceVariant = Color(0xFF2D2D2D),
    onSurfaceVariant = Color(0xFFCAC4D0),
    outline = Color(0xFF938F99)
)

/**
 * ELBIX AIDD 테마
 * - 다이나믹 컬러 지원 (Android 12+)
 * - 다크/라이트 모드 지원
 */
@Composable
fun ElbixTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = true,  // 다이나믹 컬러 사용 여부
    content: @Composable () -> Unit
) {
    val colorScheme = when {
        // Android 12+ 다이나믹 컬러
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        }
        darkTheme -> DarkColorScheme
        else -> LightColorScheme
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}
