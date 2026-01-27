package com.elbix.aidd.domain.repository

import com.elbix.aidd.domain.model.DesignRequest
import com.elbix.aidd.domain.model.DesignResult
import kotlinx.coroutines.flow.Flow

/**
 * 배전 설계 Repository 인터페이스
 * - 설계 API 호출 추상화
 */
interface DesignRepository {
    
    /**
     * 배전 설계 요청
     * 
     * @param request 설계 요청 데이터
     * @return 설계 결과
     */
    suspend fun createDesign(request: DesignRequest): Result<DesignResult>
    
    /**
     * 서버 연결 상태 확인
     * 
     * @return 연결 가능 여부
     */
    suspend fun checkServerHealth(): Boolean
}
