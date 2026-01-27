package com.elbix.aidd.domain.usecase

import com.elbix.aidd.domain.model.BoundingBox
import com.elbix.aidd.domain.model.Coordinate
import com.elbix.aidd.domain.model.FacilitiesData
import com.elbix.aidd.domain.repository.FacilitiesRepository
import javax.inject.Inject

/**
 * 시설물 조회 UseCase
 * - 시설물 조회 비즈니스 로직 캡슐화
 */
class GetFacilitiesUseCase @Inject constructor(
    private val facilitiesRepository: FacilitiesRepository
) {
    /**
     * 영역 내 시설물 조회
     * 
     * @param bbox 조회 영역
     * @param maxFeatures 최대 피처 수
     * @return 시설물 데이터
     */
    suspend operator fun invoke(
        bbox: BoundingBox,
        maxFeatures: Int = 5000
    ): Result<FacilitiesData> {
        return facilitiesRepository.getFacilities(bbox, maxFeatures)
    }
    
    /**
     * 좌표 중심 시설물 조회
     * 
     * @param center 중심 좌표
     * @param size 조회 영역 크기 (미터)
     * @param maxFeatures 최대 피처 수
     * @return 시설물 데이터
     */
    suspend fun byCenter(
        center: Coordinate,
        size: Double = 400.0,
        maxFeatures: Int = 5000
    ): Result<FacilitiesData> {
        return facilitiesRepository.getFacilitiesByCenter(center, size, maxFeatures)
    }
}
