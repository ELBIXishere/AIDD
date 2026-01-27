package com.elbix.aidd

import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.windowsizeclass.ExperimentalMaterial3WindowSizeClassApi
import androidx.compose.material3.windowsizeclass.calculateWindowSizeClass
import androidx.compose.ui.Modifier
import dagger.hilt.android.AndroidEntryPoint
import com.elbix.aidd.ui.ElbixApp
import com.elbix.aidd.ui.theme.ElbixTheme

/**
 * ELBIX AIDD 메인 액티비티
 * - 폴더블 디바이스 대응을 위한 WindowSizeClass 계산
 * - Jetpack Compose UI 설정
 */
@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    
    companion object {
        private const val TAG = "MainActivity"
    }
    
    @OptIn(ExperimentalMaterial3WindowSizeClassApi::class)
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        Log.d(TAG, "onCreate started")
        
        try {
            // Edge-to-edge 모드 활성화
            enableEdgeToEdge()
            Log.d(TAG, "enableEdgeToEdge completed")
            
            setContent {
                // 화면 크기 클래스 계산 (폴더블 대응)
                val windowSizeClass = calculateWindowSizeClass(this)
                Log.d(TAG, "windowSizeClass: ${windowSizeClass.widthSizeClass}")
                
                ElbixTheme {
                    Surface(
                        modifier = Modifier.fillMaxSize(),
                        color = MaterialTheme.colorScheme.background
                    ) {
                        // 메인 앱 컴포저블
                        ElbixApp(windowSizeClass = windowSizeClass)
                    }
                }
            }
            
            Log.d(TAG, "setContent completed")
        } catch (e: Exception) {
            Log.e(TAG, "Error in onCreate", e)
            throw e
        }
    }
}
