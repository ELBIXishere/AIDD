package com.elbix.aidd.domain.usecase

import com.elbix.aidd.domain.model.DesignRequest
import com.elbix.aidd.domain.model.DesignResult
import com.elbix.aidd.domain.repository.DesignRepository
import javax.inject.Inject

/**
 * 배전 설계 요청 UseCase
 * - 설계 비즈니스 로직 캡슐화
 */
class CreateDesignUseCase @Inject constructor(
    private val designRepository: DesignRepository
) {
    /**
     * 배전 설계 실행
     * 
     * @param request 설계 요청 데이터
     * @return 설계 결과
     */
    suspend operator fun invoke(request: DesignRequest): Result<DesignResult> {
        return designRepository.createDesign(request)
    }
}
