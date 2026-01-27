package com.elbix.aidd.data.mapper

import com.elbix.aidd.data.model.DesignRequestDto
import com.elbix.aidd.data.model.DesignResponseDto
import com.elbix.aidd.data.model.RouteResultDto
import com.elbix.aidd.data.model.VoltageDropDto
import com.elbix.aidd.domain.model.*

/**
 * 배전 설계 데이터 매퍼
 * - DTO ↔ Domain 모델 변환
 */
object DesignMapper {
    
    /**
     * 도메인 요청 → DTO 변환
     */
    fun toDto(request: DesignRequest): DesignRequestDto {
        return DesignRequestDto(
            code = "coord",
            coord = request.toCoordString(),
            phaseCode = request.phaseCode.code
        )
    }
    
    /**
     * DTO → 도메인 결과 변환
     */
    fun toDomain(dto: DesignResponseDto): DesignResult {
        return DesignResult(
            status = DesignResultStatus.fromString(dto.status),
            requestSpec = dto.requestSpec,
            consumerCoord = Coordinate.fromList(dto.consumerCoord),
            routes = dto.routes.map { toRouteDomain(it) },
            errorMessage = dto.errorMessage,
            processingTimeMs = dto.processingTimeMs,
            requestedLoadKw = dto.requestedLoadKw
        )
    }
    
    /**
     * 경로 DTO → 도메인 변환
     */
    private fun toRouteDomain(dto: RouteResultDto): RouteResult {
        return RouteResult(
            rank = dto.rank,
            totalCost = dto.totalCost,
            costIndex = dto.costIndex,
            totalDistance = dto.totalDistance,
            startPoleId = dto.startPoleId,
            startPoleCoord = Coordinate.fromList(dto.startPoleCoord),
            newPolesCount = dto.newPolesCount,
            pathCoordinates = dto.pathCoordinates.map { Coordinate.fromList(it) },
            newPoleCoordinates = dto.newPoleCoordinates.map { Coordinate.fromList(it) },
            wireCost = dto.wireCost,
            poleCost = dto.poleCost,
            laborCost = dto.laborCost,
            remark = dto.remark,
            voltageDrop = dto.voltageDrop?.let { toVoltageDropDomain(it) },
            poleSpec = dto.poleSpec,
            wireSpec = dto.wireSpec,
            sourceVoltageType = dto.sourceVoltageType,
            sourcePhaseType = dto.sourcePhaseType
        )
    }
    
    /**
     * 전압 강하 DTO → 도메인 변환
     */
    private fun toVoltageDropDomain(dto: VoltageDropDto): VoltageDrop {
        return VoltageDrop(
            distanceM = dto.distanceM,
            loadKw = dto.loadKw,
            voltageDropV = dto.voltageDropV,
            voltageDropPercent = dto.voltageDropPercent,
            isAcceptable = dto.isAcceptable,
            limitPercent = dto.limitPercent,
            wireSpec = dto.wireSpec,
            message = dto.message
        )
    }
}
