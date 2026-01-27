package com.elbix.aidd.domain.model

/**
 * 시설물 데이터 도메인 모델
 */
data class FacilitiesData(
    val poles: List<Pole>,              // 전주 목록
    val lines: List<Line>,              // 전선 목록
    val transformers: List<Transformer>,// 변압기 목록
    val roads: List<Road>,              // 도로 목록
    val buildings: List<Building>,      // 건물 목록
    val bbox: BoundingBox?              // 영역 정보
) {
    /**
     * 총 시설물 개수
     */
    val totalCount: Int
        get() = poles.size + lines.size + transformers.size + 
                roads.size + buildings.size
}

/**
 * 전주 도메인 모델
 */
data class Pole(
    val id: String,
    val coordinate: Coordinate,
    val phaseCode: PhaseCode,     // 상 코드
    val poleType: PoleType,       // 전주 유형
    val isHighVoltage: Boolean    // 고압 전주 여부
) {
    /**
     * 표시 텍스트
     */
    val displayText: String
        get() = if (isHighVoltage) "고압" else "저압"
}

/**
 * 전주 유형 열거형
 */
enum class PoleType(val code: String, val displayName: String) {
    HIGH("H", "고압"),
    LOW("L", "저압"),
    UNKNOWN("", "미상");
    
    companion object {
        fun fromCode(code: String?): PoleType {
            return entries.find { it.code == code } ?: UNKNOWN
        }
    }
}

/**
 * 전선 도메인 모델
 */
data class Line(
    val id: String,
    val coordinates: List<Coordinate>,
    val lineType: LineType,       // 전선 유형
    val phaseCode: PhaseCode      // 상 코드
)

/**
 * 전선 유형 열거형
 */
enum class LineType(val code: String, val displayName: String) {
    HIGH_VOLTAGE("HV", "고압선"),
    LOW_VOLTAGE("LV", "저압선"),
    UNKNOWN("", "미상");
    
    companion object {
        fun fromCode(code: String?): LineType {
            return when (code) {
                "HV" -> HIGH_VOLTAGE
                "LV" -> LOW_VOLTAGE
                else -> UNKNOWN
            }
        }
    }
}

/**
 * 변압기 도메인 모델
 */
data class Transformer(
    val id: String,
    val coordinate: Coordinate,
    val capacityKva: Double,      // 용량 (kVA)
    val transformerType: String?
) {
    /**
     * 용량 포맷팅
     */
    val formattedCapacity: String
        get() = "${capacityKva.toInt()} kVA"
}

/**
 * 도로 도메인 모델
 */
data class Road(
    val id: String,
    val coordinates: List<Coordinate>,
    val roadType: String?
)

/**
 * 건물 도메인 모델
 */
data class Building(
    val id: String,
    val coordinates: List<Coordinate>,  // 폴리곤 좌표
    val buildingType: String?
)

/**
 * 영역(BoundingBox) 도메인 모델
 */
data class BoundingBox(
    val minX: Double,
    val minY: Double,
    val maxX: Double,
    val maxY: Double
) {
    /**
     * API 요청용 문자열 생성
     */
    fun toQueryString(): String = "$minX,$minY,$maxX,$maxY"
    
    /**
     * 중심 좌표 계산
     */
    val center: Coordinate
        get() = Coordinate(
            x = (minX + maxX) / 2,
            y = (minY + maxY) / 2
        )
    
    companion object {
        /**
         * 중심 좌표와 크기로 BBox 생성
         */
        fun fromCenterAndSize(center: Coordinate, size: Double): BoundingBox {
            val halfSize = size / 2
            return BoundingBox(
                minX = center.x - halfSize,
                minY = center.y - halfSize,
                maxX = center.x + halfSize,
                maxY = center.y + halfSize
            )
        }
    }
}
