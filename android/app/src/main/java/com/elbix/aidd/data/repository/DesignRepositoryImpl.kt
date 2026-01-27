package com.elbix.aidd.data.repository

import android.util.Log
import com.elbix.aidd.data.api.ElbixApiService
import com.elbix.aidd.data.mapper.DesignMapper
import com.elbix.aidd.domain.model.DesignRequest
import com.elbix.aidd.domain.model.DesignResult
import com.elbix.aidd.domain.repository.DesignRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.net.ConnectException
import java.net.SocketTimeoutException
import java.net.UnknownHostException
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 배전 설계 Repository 구현체
 * - API 호출 및 데이터 변환
 */
@Singleton
class DesignRepositoryImpl @Inject constructor(
    private val apiService: ElbixApiService
) : DesignRepository {
    
    companion object {
        private const val TAG = "DesignRepository"
    }
    
    /**
     * 배전 설계 요청
     */
    override suspend fun createDesign(request: DesignRequest): Result<DesignResult> {
        return withContext(Dispatchers.IO) {
            try {
                Log.d(TAG, "Creating design for coord: (${request.coordX}, ${request.coordY})")
                
                // 도메인 → DTO 변환
                val requestDto = DesignMapper.toDto(request)
                
                // API 호출
                val response = apiService.createDesign(requestDto)
                
                if (response.isSuccessful) {
                    val body = response.body()
                    if (body != null) {
                        Log.d(TAG, "Design created successfully")
                        // DTO → 도메인 변환
                        val result = DesignMapper.toDomain(body)
                        Result.success(result)
                    } else {
                        Log.w(TAG, "Response body is null")
                        Result.failure(Exception("응답 데이터가 비어있습니다"))
                    }
                } else {
                    val errorBody = response.errorBody()?.string()
                    Log.e(TAG, "API error: ${response.code()} - $errorBody")
                    Result.failure(Exception("API 오류: ${response.code()} - $errorBody"))
                }
            } catch (e: UnknownHostException) {
                Log.e(TAG, "Unknown host exception", e)
                Result.failure(Exception("서버를 찾을 수 없습니다. 네트워크 연결을 확인하세요."))
            } catch (e: ConnectException) {
                Log.e(TAG, "Connection exception", e)
                Result.failure(Exception("서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요."))
            } catch (e: SocketTimeoutException) {
                Log.e(TAG, "Socket timeout exception", e)
                Result.failure(Exception("서버 응답 시간이 초과되었습니다."))
            } catch (e: Exception) {
                Log.e(TAG, "General exception", e)
                Result.failure(Exception("네트워크 오류: ${e.message}"))
            }
        }
    }
    
    /**
     * 서버 연결 상태 확인
     */
    override suspend fun checkServerHealth(): Boolean {
        return withContext(Dispatchers.IO) {
            try {
                Log.d(TAG, "Checking server health")
                val response = apiService.healthCheck()
                val isHealthy = response.isSuccessful
                Log.d(TAG, "Server health: $isHealthy")
                isHealthy
            } catch (e: Exception) {
                Log.e(TAG, "Health check failed", e)
                false
            }
        }
    }
}
