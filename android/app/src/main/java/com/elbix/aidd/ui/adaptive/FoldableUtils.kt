package com.elbix.aidd.ui.adaptive

import android.app.Activity
import androidx.compose.runtime.*
import androidx.compose.ui.platform.LocalContext
import androidx.window.layout.FoldingFeature
import androidx.window.layout.WindowInfoTracker
import kotlinx.coroutines.flow.collect

/**
 * 폴더블 상태 정보
 */
data class FoldableState(
    val isFolded: Boolean = false,           // 접힌 상태
    val isTableTop: Boolean = false,         // 테이블탑 모드 (반만 접음)
    val isBook: Boolean = false,             // 북 모드 (세로로 반 접음)
    val hingePosition: HingePosition? = null // 힌지 위치
)

/**
 * 힌지 위치 정보
 */
data class HingePosition(
    val left: Int,
    val top: Int,
    val right: Int,
    val bottom: Int
) {
    val width: Int get() = right - left
    val height: Int get() = bottom - top
}

/**
 * 폴더블 상태 감지 Composable
 * - WindowInfoTracker를 통해 폴딩 상태 모니터링
 */
@Composable
fun rememberFoldableState(): FoldableState {
    val context = LocalContext.current
    var foldableState by remember { mutableStateOf(FoldableState()) }
    
    LaunchedEffect(context) {
        if (context is Activity) {
            val windowInfoTracker = WindowInfoTracker.getOrCreate(context)
            
            windowInfoTracker.windowLayoutInfo(context).collect { layoutInfo ->
                val foldingFeature = layoutInfo.displayFeatures
                    .filterIsInstance<FoldingFeature>()
                    .firstOrNull()
                
                foldableState = if (foldingFeature != null) {
                    FoldableState(
                        isFolded = foldingFeature.state == FoldingFeature.State.HALF_OPENED,
                        isTableTop = foldingFeature.orientation == FoldingFeature.Orientation.HORIZONTAL &&
                                    foldingFeature.state == FoldingFeature.State.HALF_OPENED,
                        isBook = foldingFeature.orientation == FoldingFeature.Orientation.VERTICAL &&
                                foldingFeature.state == FoldingFeature.State.HALF_OPENED,
                        hingePosition = HingePosition(
                            left = foldingFeature.bounds.left,
                            top = foldingFeature.bounds.top,
                            right = foldingFeature.bounds.right,
                            bottom = foldingFeature.bounds.bottom
                        )
                    )
                } else {
                    FoldableState()
                }
            }
        }
    }
    
    return foldableState
}

/**
 * 폴더블 디바이스 여부 확인
 */
@Composable
fun isFoldableDevice(): Boolean {
    val context = LocalContext.current
    var isFoldable by remember { mutableStateOf(false) }
    
    LaunchedEffect(context) {
        if (context is Activity) {
            val windowInfoTracker = WindowInfoTracker.getOrCreate(context)
            
            windowInfoTracker.windowLayoutInfo(context).collect { layoutInfo ->
                isFoldable = layoutInfo.displayFeatures
                    .filterIsInstance<FoldingFeature>()
                    .isNotEmpty()
            }
        }
    }
    
    return isFoldable
}

/**
 * Galaxy Z Fold 시리즈 최적화
 * - 커버 스크린 (접힘): 약 904 x 2316 px
 * - 메인 스크린 (펼침): 약 1812 x 2176 px
 */
object GalaxyFoldOptimization {
    // 접힌 상태 최대 너비 (dp)
    const val COVER_SCREEN_MAX_WIDTH = 360
    
    // 펼친 상태 최소 너비 (dp)
    const val MAIN_SCREEN_MIN_WIDTH = 600
    
    /**
     * 현재 화면 크기에 따른 모드 판단
     */
    fun getScreenMode(widthDp: Int): ScreenMode {
        return when {
            widthDp <= COVER_SCREEN_MAX_WIDTH -> ScreenMode.COVER
            widthDp >= MAIN_SCREEN_MIN_WIDTH -> ScreenMode.MAIN
            else -> ScreenMode.MEDIUM
        }
    }
}

/**
 * 화면 모드 열거형
 */
enum class ScreenMode {
    COVER,  // 커버 스크린 (접힘)
    MEDIUM, // 중간 크기
    MAIN    // 메인 스크린 (펼침)
}
