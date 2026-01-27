package com.elbix.aidd.domain.model

/**
 * 배전 설계 요청 도메인 모델
 */
data class DesignRequest(
    val coordX: Double,          // 수용가 X 좌표 (EPSG:3857)
    val coordY: Double,          // 수용가 Y 좌표 (EPSG:3857)
    val phaseCode: PhaseCode     // 신청 규격 (단상/3상)
) {
    /**
     * API 요청용 좌표 문자열 생성
     */
    fun toCoordString(): String = "$coordX,$coordY"
}

/**
 * 상(Phase) 코드 열거형
 */
enum class PhaseCode(val code: String, val displayName: String) {
    SINGLE("1", "단상"),
    THREE("3", "3상");
    
    companion object {
        fun fromCode(code: String): PhaseCode {
            return entries.find { it.code == code } ?: SINGLE
        }
    }
}

/**
 * 배전 설계 결과 도메인 모델
 */
data class DesignResult(
    val status: DesignResultStatus,      // 처리 상태
    val requestSpec: String,             // 요청 규격 (한글)
    val consumerCoord: Coordinate,       // 수용가 좌표
    val routes: List<RouteResult>,       // 경로 목록
    val errorMessage: String?,           // 오류 메시지
    val processingTimeMs: Int?,          // 처리 시간
    val requestedLoadKw: Double?         // 요청 부하
) {
    /**
     * 성공 여부
     */
    val isSuccess: Boolean
        get() = status == DesignResultStatus.SUCCESS && routes.isNotEmpty()
}

/**
 * 설계 결과 상태
 */
enum class DesignResultStatus {
    SUCCESS,        // 성공
    FAILED,         // 실패
    NO_ROUTE,       // 경로 없음
    OVER_DISTANCE;  // 거리 초과
    
    companion object {
        fun fromString(value: String): DesignResultStatus {
            return when (value) {
                "Success" -> SUCCESS
                "NoRoute" -> NO_ROUTE
                "OverDistance" -> OVER_DISTANCE
                else -> FAILED
            }
        }
    }
}

/**
 * 개별 경로 결과 도메인 모델
 */
data class RouteResult(
    val rank: Int,                         // 순위
    val totalCost: Int,                    // 예상 공사비 (원)
    val costIndex: Int,                    // 공사비 환산 점수
    val totalDistance: Double,             // 총 거리 (m)
    val startPoleId: String,               // 시작 전주 ID
    val startPoleCoord: Coordinate,        // 시작 전주 좌표
    val newPolesCount: Int,                // 신설 전주 개수
    val pathCoordinates: List<Coordinate>, // 경로 좌표
    val newPoleCoordinates: List<Coordinate>, // 신설 전주 좌표
    val wireCost: Int,                     // 전선 비용
    val poleCost: Int,                     // 전주 비용
    val laborCost: Int,                    // 노무비
    val remark: String?,                   // 비고
    val voltageDrop: VoltageDrop?,         // 전압 강하 정보
    val poleSpec: String?,                 // 전주 규격
    val wireSpec: String?,                 // 전선 규격
    val sourceVoltageType: String?,        // 기설 전주 전압 유형
    val sourcePhaseType: String?           // 기설 전주 상 유형
) {
    /**
     * 공사비 포맷팅 (천 단위 콤마)
     */
    val formattedCost: String
        get() = String.format("%,d", totalCost)
    
    /**
     * 거리 포맷팅
     */
    val formattedDistance: String
        get() = String.format("%.1f", totalDistance)
    
    /**
     * Fast Track 여부
     */
    val isFastTrack: Boolean
        get() = remark?.contains("FastTrack") == true
}

/**
 * 전압 강하 정보 도메인 모델
 */
data class VoltageDrop(
    val distanceM: Double,          // 거리 (m)
    val loadKw: Double,             // 부하 (kW)
    val voltageDropV: Double,       // 전압 강하 (V)
    val voltageDropPercent: Double, // 전압 강하율 (%)
    val isAcceptable: Boolean,      // 허용 범위 내 여부
    val limitPercent: Double,       // 허용 한계 (%)
    val wireSpec: String?,          // 전선 규격
    val message: String?            // 결과 메시지
) {
    /**
     * 전압 강하율 포맷팅
     */
    val formattedPercent: String
        get() = String.format("%.2f", voltageDropPercent)
}

/**
 * 좌표 도메인 모델
 */
data class Coordinate(
    val x: Double,  // X 좌표 (EPSG:3857)
    val y: Double   // Y 좌표 (EPSG:3857)
) {
    companion object {
        /**
         * 리스트에서 좌표 생성
         */
        fun fromList(list: List<Double>): Coordinate {
            require(list.size >= 2) { "좌표 리스트는 최소 2개 요소 필요" }
            return Coordinate(list[0], list[1])
        }
    }
    
    /**
     * 문자열로 변환
     */
    override fun toString(): String = "$x,$y"
}
