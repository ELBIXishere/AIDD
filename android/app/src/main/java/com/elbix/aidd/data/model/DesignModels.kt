package com.elbix.aidd.data.model

import com.google.gson.annotations.SerializedName

/**
 * 배전 설계 요청 DTO
 * - 백엔드 /api/v1/design API 요청 바디
 */
data class DesignRequestDto(
    // 입력 타입 (기본: 좌표)
    @SerializedName("code")
    val code: String = "coord",
    
    // 수용가 좌표 (EPSG:3857, "x,y" 형식)
    @SerializedName("coord")
    val coord: String,
    
    // 신청 규격 ("1": 단상, "3": 3상)
    @SerializedName("phase_code")
    val phaseCode: String = "1"
)

/**
 * 배전 설계 응답 DTO
 * - 백엔드 /api/v1/design API 응답
 */
data class DesignResponseDto(
    // 처리 상태
    @SerializedName("status")
    val status: String,
    
    // 요청 규격 (한글: 단상/3상)
    @SerializedName("request_spec")
    val requestSpec: String,
    
    // 수용가 좌표 [x, y]
    @SerializedName("consumer_coord")
    val consumerCoord: List<Double>,
    
    // 경로 목록 (공사비 오름차순)
    @SerializedName("routes")
    val routes: List<RouteResultDto> = emptyList(),
    
    // 오류 메시지 (실패 시)
    @SerializedName("error_message")
    val errorMessage: String? = null,
    
    // 처리 시간 (밀리초)
    @SerializedName("processing_time_ms")
    val processingTimeMs: Int? = null,
    
    // 요청 부하 (kW)
    @SerializedName("requested_load_kw")
    val requestedLoadKw: Double? = null
)

/**
 * 개별 경로 결과 DTO
 */
data class RouteResultDto(
    // 순위 (cost_index 기준, 1이 최저 비용)
    @SerializedName("rank")
    val rank: Int,
    
    // 예상 총 공사비 (원)
    @SerializedName("total_cost")
    val totalCost: Int,
    
    // 공사비 환산 점수
    @SerializedName("cost_index")
    val costIndex: Int = 0,
    
    // 총 경로 거리 (미터)
    @SerializedName("total_distance")
    val totalDistance: Double,
    
    // 시작 기설전주 ID
    @SerializedName("start_pole_id")
    val startPoleId: String,
    
    // 시작 기설전주 좌표 [x, y]
    @SerializedName("start_pole_coord")
    val startPoleCoord: List<Double>,
    
    // 신설 전주 개수
    @SerializedName("new_poles_count")
    val newPolesCount: Int,
    
    // 전체 경로 좌표 [[x1, y1], [x2, y2], ...]
    @SerializedName("path_coordinates")
    val pathCoordinates: List<List<Double>>,
    
    // 신설 전주 좌표
    @SerializedName("new_pole_coordinates")
    val newPoleCoordinates: List<List<Double>> = emptyList(),
    
    // 전선 비용 (원)
    @SerializedName("wire_cost")
    val wireCost: Int = 0,
    
    // 전주 비용 (원)
    @SerializedName("pole_cost")
    val poleCost: Int = 0,
    
    // 노무비 (원)
    @SerializedName("labor_cost")
    val laborCost: Int = 0,
    
    // 비고
    @SerializedName("remark")
    val remark: String? = null,
    
    // 전압 강하 정보
    @SerializedName("voltage_drop")
    val voltageDrop: VoltageDropDto? = null,
    
    // 전주 규격
    @SerializedName("pole_spec")
    val poleSpec: String? = null,
    
    // 전선 규격
    @SerializedName("wire_spec")
    val wireSpec: String? = null,
    
    // 기설 전주 전압 유형 (HV: 고압, LV: 저압)
    @SerializedName("source_voltage_type")
    val sourceVoltageType: String? = null,
    
    // 기설 전주 상 유형 (1: 단상, 3: 3상)
    @SerializedName("source_phase_type")
    val sourcePhaseType: String? = null
)

/**
 * 전압 강하 정보 DTO
 */
data class VoltageDropDto(
    // 거리 (m)
    @SerializedName("distance_m")
    val distanceM: Double = 0.0,
    
    // 부하 (kW)
    @SerializedName("load_kw")
    val loadKw: Double = 0.0,
    
    // 전압 강하 (V)
    @SerializedName("voltage_drop_v")
    val voltageDropV: Double = 0.0,
    
    // 전압 강하율 (%)
    @SerializedName("voltage_drop_percent")
    val voltageDropPercent: Double = 0.0,
    
    // 허용 범위 내 여부
    @SerializedName("is_acceptable")
    val isAcceptable: Boolean = true,
    
    // 허용 한계 (%)
    @SerializedName("limit_percent")
    val limitPercent: Double = 6.0,
    
    // 전선 규격
    @SerializedName("wire_spec")
    val wireSpec: String? = null,
    
    // 결과 메시지
    @SerializedName("message")
    val message: String? = null
)

/**
 * 설계 상태 열거형
 */
enum class DesignStatus(val value: String) {
    SUCCESS("Success"),
    FAILED("Failed"),
    NO_ROUTE("NoRoute"),
    OVER_DISTANCE("OverDistance");
    
    companion object {
        fun fromValue(value: String): DesignStatus {
            return entries.find { it.value == value } ?: FAILED
        }
    }
}
