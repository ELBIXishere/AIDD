package com.elbix.aidd.domain.repository

import com.elbix.aidd.domain.model.BoundingBox
import com.elbix.aidd.domain.model.Coordinate
import com.elbix.aidd.domain.model.FacilitiesData

/**
 * 시설물 Repository 인터페이스
 * - 시설물 조회 API 호출 추상화
 */
interface FacilitiesRepository {
    
    /**
     * 영역 내 시설물 조회
     * 
     * @param bbox 조회 영역
     * @param maxFeatures 최대 피처 수
     * @return 시설물 데이터
     */
    suspend fun getFacilities(
        bbox: BoundingBox,
        maxFeatures: Int = 5000
    ): Result<FacilitiesData>
    
    /**
     * 좌표 중심 시설물 조회
     * 
     * @param center 중심 좌표
     * @param size 조회 영역 크기 (미터)
     * @param maxFeatures 최대 피처 수
     * @return 시설물 데이터
     */
    suspend fun getFacilitiesByCenter(
        center: Coordinate,
        size: Double = 400.0,
        maxFeatures: Int = 5000
    ): Result<FacilitiesData>
}
