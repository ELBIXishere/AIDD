package com.elbix.aidd.data.api

import com.elbix.aidd.data.model.DesignRequestDto
import com.elbix.aidd.data.model.DesignResponseDto
import com.elbix.aidd.data.model.FacilitiesResponseDto
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Query

/**
 * ELBIX AIDD 백엔드 API 서비스 인터페이스
 * - Retrofit을 통한 REST API 호출 정의
 */
interface ElbixApiService {
    
    /**
     * 헬스 체크
     * - 서버 상태 확인
     */
    @GET("health")
    suspend fun healthCheck(): Response<Map<String, String>>
    
    /**
     * 배전 설계 요청
     * - 수용가 좌표와 신청 규격을 입력받아 최적의 배전 경로 계산
     * 
     * @param request 설계 요청 데이터 (좌표, 상 코드)
     * @return 설계 결과 (경로 목록, 공사비 등)
     */
    @POST("api/v1/design")
    suspend fun createDesign(
        @Body request: DesignRequestDto
    ): Response<DesignResponseDto>
    
    /**
     * 시설물 조회
     * - 지정된 영역 내의 모든 시설물 조회
     * 
     * @param bbox 영역 (EPSG:3857, "minX,minY,maxX,maxY" 형식)
     * @param maxFeatures 레이어별 최대 피처 수 (기본 5000, 최대 5000)
     * @return 시설물 데이터 (전주, 전선, 변압기, 도로, 건물 등)
     */
    @GET("api/v1/facilities")
    suspend fun getFacilities(
        @Query("bbox") bbox: String,
        @Query("max_features") maxFeatures: Int = 5000
    ): Response<FacilitiesResponseDto>
    
    /**
     * 시설물 조회 (좌표 기반 - deprecated)
     * - 중심 좌표와 영역 크기로 시설물 조회
     * 
     * @param coord 중심 좌표 (EPSG:3857, "x,y" 형식)
     * @param bboxSize 조회 영역 크기 (미터, 기본 400)
     * @param maxFeatures 레이어별 최대 피처 수
     * @return 시설물 데이터
     */
    @GET("api/v1/facilities")
    suspend fun getFacilitiesByCoord(
        @Query("coord") coord: String,
        @Query("bbox_size") bboxSize: Double = 400.0,
        @Query("max_features") maxFeatures: Int = 5000
    ): Response<FacilitiesResponseDto>
    
    /**
     * 설계 서비스 상태 확인
     * - 설계 서비스 가용 상태 및 설정 확인
     */
    @GET("api/v1/design/status")
    suspend fun getDesignStatus(): Response<DesignStatusResponse>
}

/**
 * 설계 상태 응답 DTO
 */
data class DesignStatusResponse(
    val service: String,
    val status: String,
    val max_distance_limit: Double,
    val supported_phases: List<String>
)
