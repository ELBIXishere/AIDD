package com.elbix.aidd.data.model

import com.google.gson.annotations.SerializedName

/**
 * 시설물 조회 응답 DTO
 * - 백엔드 /api/v1/facilities API 응답
 */
data class FacilitiesResponseDto(
    // 전주 목록
    @SerializedName("poles")
    val poles: List<PoleDto> = emptyList(),
    
    // 전선 목록
    @SerializedName("lines")
    val lines: List<LineDto> = emptyList(),
    
    // 변압기 목록
    @SerializedName("transformers")
    val transformers: List<TransformerDto> = emptyList(),
    
    // 도로 목록
    @SerializedName("roads")
    val roads: List<RoadDto> = emptyList(),
    
    // 건물 목록
    @SerializedName("buildings")
    val buildings: List<BuildingDto> = emptyList(),
    
    // 철도 목록
    @SerializedName("railways")
    val railways: List<RailwayDto> = emptyList(),
    
    // 하천 목록
    @SerializedName("rivers")
    val rivers: List<RiverDto> = emptyList(),
    
    // 개수 정보
    @SerializedName("count")
    val count: CountDto? = null,
    
    // 영역 정보
    @SerializedName("bbox")
    val bbox: BboxDto? = null
)

/**
 * 전주 DTO
 */
data class PoleDto(
    @SerializedName("id")
    val id: String,
    
    // 좌표 [x, y]
    @SerializedName("coordinates")
    val coordinates: List<Double>,
    
    // 상 코드 ("1": 단상, "3": 3상)
    @SerializedName("phase_code")
    val phaseCode: String? = null,
    
    // 전주 유형
    @SerializedName("pole_type")
    val poleType: String? = null,
    
    // 고압 전주 여부
    @SerializedName("is_high_voltage")
    val isHighVoltage: Boolean = false
)

/**
 * 전선 DTO
 */
data class LineDto(
    @SerializedName("id")
    val id: String,
    
    // 좌표 [[x1, y1], [x2, y2], ...]
    @SerializedName("coordinates")
    val coordinates: List<List<Double>>,
    
    // 전선 유형 (HV: 고압, LV: 저압)
    @SerializedName("line_type")
    val lineType: String? = null,
    
    // 상 코드
    @SerializedName("phase_code")
    val phaseCode: String? = null
)

/**
 * 변압기 DTO
 */
data class TransformerDto(
    @SerializedName("id")
    val id: String,
    
    // 좌표 (포인트 또는 라인)
    @SerializedName("coordinates")
    val coordinates: List<Any>,
    
    // 용량 (kVA)
    @SerializedName("capacity_kva")
    val capacityKva: Double = 0.0,
    
    // 변압기 유형
    @SerializedName("transformer_type")
    val transformerType: String? = null
)

/**
 * 도로 DTO
 */
data class RoadDto(
    @SerializedName("id")
    val id: String,
    
    // 좌표 [[x1, y1], [x2, y2], ...]
    @SerializedName("coordinates")
    val coordinates: List<List<Double>>,
    
    // 도로 유형
    @SerializedName("road_type")
    val roadType: String? = null
)

/**
 * 건물 DTO
 */
data class BuildingDto(
    @SerializedName("id")
    val id: String,
    
    // 좌표 (폴리곤)
    @SerializedName("coordinates")
    val coordinates: List<List<Double>>,
    
    // 건물 유형
    @SerializedName("building_type")
    val buildingType: String? = null
)

/**
 * 철도 DTO
 */
data class RailwayDto(
    @SerializedName("id")
    val id: String,
    
    @SerializedName("coordinates")
    val coordinates: List<Any>,
    
    @SerializedName("railway_type")
    val railwayType: String? = null
)

/**
 * 하천 DTO
 */
data class RiverDto(
    @SerializedName("id")
    val id: String,
    
    @SerializedName("coordinates")
    val coordinates: List<Any>,
    
    @SerializedName("river_type")
    val riverType: String? = null
)

/**
 * 개수 정보 DTO
 */
data class CountDto(
    @SerializedName("poles")
    val poles: Int = 0,
    
    @SerializedName("lines")
    val lines: Int = 0,
    
    @SerializedName("transformers")
    val transformers: Int = 0,
    
    @SerializedName("roads")
    val roads: Int = 0,
    
    @SerializedName("buildings")
    val buildings: Int = 0,
    
    @SerializedName("railways")
    val railways: Int = 0,
    
    @SerializedName("rivers")
    val rivers: Int = 0
)

/**
 * 영역 정보 DTO
 */
data class BboxDto(
    @SerializedName("min")
    val min: List<Double>,
    
    @SerializedName("max")
    val max: List<Double>
)
