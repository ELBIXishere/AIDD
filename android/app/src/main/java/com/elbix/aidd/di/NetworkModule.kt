package com.elbix.aidd.di

import com.elbix.aidd.BuildConfig
import com.elbix.aidd.data.api.ElbixApiService
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

/**
 * 네트워크 관련 의존성 주입 모듈
 * - OkHttp 클라이언트
 * - Retrofit 인스턴스
 * - API 서비스
 */
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    
    /**
     * OkHttp 클라이언트 제공
     * - 타임아웃 설정 (설계 API가 오래 걸릴 수 있으므로 충분히 설정)
     * - 로깅 인터셉터 (디버그 빌드)
     */
    @Provides
    @Singleton
    fun provideOkHttpClient(): OkHttpClient {
        val builder = OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(120, TimeUnit.SECONDS)  // 설계 API 대응: 2분
            .writeTimeout(30, TimeUnit.SECONDS)
        
        // 디버그 빌드에서 로깅 활성화
        if (BuildConfig.DEBUG) {
            val loggingInterceptor = HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BODY
            }
            builder.addInterceptor(loggingInterceptor)
        }
        
        return builder.build()
    }
    
    /**
     * Retrofit 인스턴스 제공
     * - ELBIX AIDD 백엔드 서버 연결
     */
    @Provides
    @Singleton
    fun provideRetrofit(okHttpClient: OkHttpClient): Retrofit {
        return Retrofit.Builder()
            .baseUrl(BuildConfig.API_BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }
    
    /**
     * ELBIX API 서비스 제공
     */
    @Provides
    @Singleton
    fun provideElbixApiService(retrofit: Retrofit): ElbixApiService {
        return retrofit.create(ElbixApiService::class.java)
    }
}
