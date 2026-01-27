package com.elbix.aidd.data.repository

import android.util.Log
import com.elbix.aidd.data.api.ElbixApiService
import com.elbix.aidd.data.mapper.FacilitiesMapper
import com.elbix.aidd.domain.model.BoundingBox
import com.elbix.aidd.domain.model.Coordinate
import com.elbix.aidd.domain.model.FacilitiesData
import com.elbix.aidd.domain.repository.FacilitiesRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.net.ConnectException
import java.net.SocketTimeoutException
import java.net.UnknownHostException
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 시설물 Repository 구현체
 * - API 호출 및 데이터 변환
 */
@Singleton
class FacilitiesRepositoryImpl @Inject constructor(
    private val apiService: ElbixApiService
) : FacilitiesRepository {
    
    companion object {
        private const val TAG = "FacilitiesRepository"
    }
    
    /**
     * 영역 내 시설물 조회
     */
    override suspend fun getFacilities(
        bbox: BoundingBox,
        maxFeatures: Int
    ): Result<FacilitiesData> {
        return withContext(Dispatchers.IO) {
            try {
                Log.d(TAG, "Fetching facilities for bbox: ${bbox.toQueryString()}")
                
                // API 호출
                val response = apiService.getFacilities(
                    bbox = bbox.toQueryString(),
                    maxFeatures = maxFeatures
                )
                
                if (response.isSuccessful) {
                    val body = response.body()
                    if (body != null) {
                        Log.d(TAG, "API response received successfully")
                        // DTO → 도메인 변환
                        val result = FacilitiesMapper.toDomain(body)
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
     * 좌표 중심 시설물 조회
     */
    override suspend fun getFacilitiesByCenter(
        center: Coordinate,
        size: Double,
        maxFeatures: Int
    ): Result<FacilitiesData> {
        // BBox 생성 후 조회
        val bbox = BoundingBox.fromCenterAndSize(center, size)
        return getFacilities(bbox, maxFeatures)
    }
}
