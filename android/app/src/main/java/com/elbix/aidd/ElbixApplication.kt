package com.elbix.aidd

import android.app.Application
import android.util.Log
import dagger.hilt.android.HiltAndroidApp
import org.osmdroid.config.Configuration
import java.io.File

/**
 * ELBIX AIDD 애플리케이션 클래스
 * - Hilt DI 컨테이너 초기화
 * - OSMDroid 지도 초기화
 */
@HiltAndroidApp
class ElbixApplication : Application() {
    
    companion object {
        private const val TAG = "ElbixApplication"
    }
    
    override fun onCreate() {
        super.onCreate()
        Log.d(TAG, "Application onCreate started")
        
        try {
            // OSMDroid 초기화
            initOsmdroid()
            Log.d(TAG, "OSMDroid initialized successfully")
        } catch (e: Exception) {
            Log.e(TAG, "Error initializing OSMDroid", e)
        }
        
        Log.d(TAG, "Application onCreate completed")
    }
    
    /**
     * OSMDroid 지도 라이브러리 초기화
     */
    private fun initOsmdroid() {
        // OSMDroid 설정 로드
        val config = Configuration.getInstance()
        
        // User-Agent 설정 (OpenStreetMap 정책 준수)
        config.userAgentValue = packageName
        
        // 타일 캐시 디렉토리 설정 (앱 내부 저장소 사용)
        val osmdroidBasePath = File(cacheDir, "osmdroid")
        config.osmdroidBasePath = osmdroidBasePath
        
        val osmdroidTileCache = File(osmdroidBasePath, "tiles")
        config.osmdroidTileCache = osmdroidTileCache
        
        // 디렉토리 생성
        if (!osmdroidBasePath.exists()) {
            osmdroidBasePath.mkdirs()
        }
        if (!osmdroidTileCache.exists()) {
            osmdroidTileCache.mkdirs()
        }
        
        Log.d(TAG, "OSMDroid cache path: ${osmdroidBasePath.absolutePath}")
    }
}
