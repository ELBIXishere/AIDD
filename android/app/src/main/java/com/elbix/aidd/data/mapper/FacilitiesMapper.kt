package com.elbix.aidd.data.mapper

import com.elbix.aidd.data.model.*
import com.elbix.aidd.domain.model.*

/**
 * 시설물 데이터 매퍼
 * - DTO ↔ Domain 모델 변환
 */
object FacilitiesMapper {
    
    /**
     * DTO → 도메인 변환
     */
    fun toDomain(dto: FacilitiesResponseDto): FacilitiesData {
        return FacilitiesData(
            poles = dto.poles.mapNotNull { toPoleDomain(it) },
            lines = dto.lines.mapNotNull { toLineDomain(it) },
            transformers = dto.transformers.mapNotNull { toTransformerDomain(it) },
            roads = dto.roads.mapNotNull { toRoadDomain(it) },
            buildings = dto.buildings.mapNotNull { toBuildingDomain(it) },
            bbox = dto.bbox?.let { toBboxDomain(it) }
        )
    }
    
    /**
     * 전주 DTO → 도메인 변환
     */
    private fun toPoleDomain(dto: PoleDto): Pole? {
        return try {
            if (dto.coordinates.size < 2) return null
            
            Pole(
                id = dto.id,
                coordinate = Coordinate(dto.coordinates[0], dto.coordinates[1]),
                phaseCode = PhaseCode.fromCode(dto.phaseCode ?: "1"),
                poleType = PoleType.fromCode(dto.poleType),
                isHighVoltage = dto.isHighVoltage
            )
        } catch (e: Exception) {
            null
        }
    }
    
    /**
     * 전선 DTO → 도메인 변환
     */
    private fun toLineDomain(dto: LineDto): Line? {
        return try {
            if (dto.coordinates.size < 2) return null
            
            Line(
                id = dto.id,
                coordinates = dto.coordinates.mapNotNull { coords ->
                    if (coords.size >= 2) Coordinate(coords[0], coords[1]) else null
                },
                lineType = LineType.fromCode(dto.lineType),
                phaseCode = PhaseCode.fromCode(dto.phaseCode ?: "1")
            )
        } catch (e: Exception) {
            null
        }
    }
    
    /**
     * 변압기 DTO → 도메인 변환
     */
    private fun toTransformerDomain(dto: TransformerDto): Transformer? {
        return try {
            // 좌표 파싱 (포인트 또는 라인의 첫 좌표)
            val coordinate = parseTransformerCoordinate(dto.coordinates)
                ?: return null
            
            Transformer(
                id = dto.id,
                coordinate = coordinate,
                capacityKva = dto.capacityKva,
                transformerType = dto.transformerType
            )
        } catch (e: Exception) {
            null
        }
    }
    
    /**
     * 변압기 좌표 파싱
     * - 포인트: [x, y]
     * - 라인: [[x1, y1], [x2, y2], ...]
     */
    @Suppress("UNCHECKED_CAST")
    private fun parseTransformerCoordinate(coordinates: List<Any>): Coordinate? {
        if (coordinates.isEmpty()) return null
        
        return try {
            when (val first = coordinates[0]) {
                is Double -> {
                    // 포인트: [x, y]
                    if (coordinates.size >= 2) {
                        Coordinate(first, coordinates[1] as Double)
                    } else null
                }
                is List<*> -> {
                    // 라인: [[x1, y1], ...] → 첫 좌표 사용
                    val firstCoord = first as? List<Double>
                    if (firstCoord != null && firstCoord.size >= 2) {
                        Coordinate(firstCoord[0], firstCoord[1])
                    } else null
                }
                else -> null
            }
        } catch (e: Exception) {
            null
        }
    }
    
    /**
     * 도로 DTO → 도메인 변환
     */
    private fun toRoadDomain(dto: RoadDto): Road? {
        return try {
            if (dto.coordinates.size < 2) return null
            
            Road(
                id = dto.id,
                coordinates = dto.coordinates.mapNotNull { coords ->
                    if (coords.size >= 2) Coordinate(coords[0], coords[1]) else null
                },
                roadType = dto.roadType
            )
        } catch (e: Exception) {
            null
        }
    }
    
    /**
     * 건물 DTO → 도메인 변환
     */
    private fun toBuildingDomain(dto: BuildingDto): Building? {
        return try {
            if (dto.coordinates.size < 3) return null
            
            Building(
                id = dto.id,
                coordinates = dto.coordinates.mapNotNull { coords ->
                    if (coords.size >= 2) Coordinate(coords[0], coords[1]) else null
                },
                buildingType = dto.buildingType
            )
        } catch (e: Exception) {
            null
        }
    }
    
    /**
     * BBox DTO → 도메인 변환
     */
    private fun toBboxDomain(dto: BboxDto): BoundingBox? {
        return try {
            if (dto.min.size < 2 || dto.max.size < 2) return null
            
            BoundingBox(
                minX = dto.min[0],
                minY = dto.min[1],
                maxX = dto.max[0],
                maxY = dto.max[1]
            )
        } catch (e: Exception) {
            null
        }
    }
}
