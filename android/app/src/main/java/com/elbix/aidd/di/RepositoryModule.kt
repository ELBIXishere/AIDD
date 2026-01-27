package com.elbix.aidd.di

import com.elbix.aidd.data.repository.DesignRepositoryImpl
import com.elbix.aidd.data.repository.FacilitiesRepositoryImpl
import com.elbix.aidd.domain.repository.DesignRepository
import com.elbix.aidd.domain.repository.FacilitiesRepository
import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

/**
 * Repository 의존성 주입 모듈
 * - Repository 인터페이스와 구현체 바인딩
 */
@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {
    
    /**
     * 설계 Repository 바인딩
     */
    @Binds
    @Singleton
    abstract fun bindDesignRepository(
        designRepositoryImpl: DesignRepositoryImpl
    ): DesignRepository
    
    /**
     * 시설물 Repository 바인딩
     */
    @Binds
    @Singleton
    abstract fun bindFacilitiesRepository(
        facilitiesRepositoryImpl: FacilitiesRepositoryImpl
    ): FacilitiesRepository
}
