package com.elbix.aidd.ui.main

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.elbix.aidd.domain.model.*
import com.elbix.aidd.domain.usecase.CreateDesignUseCase
import com.elbix.aidd.domain.usecase.GetFacilitiesUseCase
import com.elbix.aidd.util.CoordinateUtils
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * 통합 메인 화면 ViewModel
 * - 지도 상태 관리 (위치, 줌)
 * - 시설물 데이터 관리
 * - 설계 요청 및 결과 관리
 */
@HiltViewModel
class MainViewModel @Inject constructor(
    private val getFacilitiesUseCase: GetFacilitiesUseCase,
    private val createDesignUseCase: CreateDesignUseCase
) : ViewModel() {
    
    companion object {
        private const val TAG = "MainViewModel"
    }
    
    private val _uiState = MutableStateFlow(MainUiState())
    val uiState: StateFlow<MainUiState> = _uiState.asStateFlow()
    
    // 마지막 조회 영역 (중복 방지)
    private var lastBbox: BoundingBox? = null
    
    // ===== 지도 상태 관리 =====
    
    /**
     * 지도 중심 및 줌 레벨 업데이트
     */
    fun updateMapState(centerLat: Double, centerLng: Double, zoom: Double) {
        _uiState.update { 
            it.copy(
                mapState = it.mapState.copy(
                    centerLat = centerLat,
                    centerLng = centerLng,
                    zoom = zoom
                )
            )
        }
    }
    
    /**
     * 특정 좌표로 지도 이동
     */
    fun moveToCoordinate(coordinate: Coordinate) {
        val (lat, lng) = CoordinateUtils.epsg3857ToWgs84(coordinate.x, coordinate.y)
        _uiState.update { 
            it.copy(
                mapState = it.mapState.copy(
                    centerLat = lat,
                    centerLng = lng,
                    zoom = 17.0  // 확대하여 이동
                ),
                selectedCoord = coordinate
            )
        }
        
        // 지도 이동 트리거
        _uiState.update { it.copy(mapMoveRequest = coordinate) }
    }
    
    /**
     * 지도 이동 완료 처리
     */
    fun onMapMoveCompleted() {
        _uiState.update { it.copy(mapMoveRequest = null) }
    }
    
    // ===== 좌표 선택 관리 =====
    
    /**
     * 지도에서 좌표 선택
     */
    fun selectCoordinate(coordinate: Coordinate) {
        _uiState.update { 
            it.copy(
                selectedCoord = coordinate,
                coordX = String.format("%.2f", coordinate.x),
                coordY = String.format("%.2f", coordinate.y)
            )
        }
    }
    
    /**
     * X 좌표 직접 입력
     */
    fun updateCoordX(value: String) {
        _uiState.update { it.copy(coordX = value) }
    }
    
    /**
     * Y 좌표 직접 입력
     */
    fun updateCoordY(value: String) {
        _uiState.update { it.copy(coordY = value) }
    }
    
    /**
     * 좌표 선택 취소
     */
    fun clearCoordinate() {
        _uiState.update { 
            it.copy(
                selectedCoord = null,
                coordX = "",
                coordY = "",
                designResult = null
            )
        }
    }
    
    /**
     * 상 코드 변경
     */
    fun updatePhaseCode(phaseCode: PhaseCode) {
        _uiState.update { it.copy(phaseCode = phaseCode) }
    }
    
    // ===== 시설물 관리 =====
    
    /**
     * 시설물 표시 토글
     */
    fun toggleFacilitiesVisible(visible: Boolean) {
        _uiState.update { it.copy(showFacilities = visible) }
        
        // ON으로 변경 시 현재 영역 시설물 로드
        if (visible && _uiState.value.facilities == null) {
            lastBbox?.let { loadFacilities(it) }
        }
    }
    
    /**
     * 시설물 데이터 로드
     */
    fun loadFacilities(bbox: BoundingBox) {
        // 시설물 표시가 OFF면 로드하지 않음
        if (!_uiState.value.showFacilities) {
            lastBbox = bbox
            return
        }
        
        // 동일 영역 중복 조회 방지
        if (bbox == lastBbox && _uiState.value.facilities != null) return
        lastBbox = bbox
        
        viewModelScope.launch {
            _uiState.update { it.copy(isFacilitiesLoading = true) }
            
            try {
                Log.d(TAG, "Loading facilities for bbox: $bbox")
                
                getFacilitiesUseCase(bbox)
                    .onSuccess { facilities ->
                        Log.d(TAG, "Facilities loaded: poles=${facilities.poles.size}")
                        _uiState.update { 
                            it.copy(
                                isFacilitiesLoading = false,
                                facilities = facilities
                            )
                        }
                    }
                    .onFailure { error ->
                        Log.e(TAG, "Failed to load facilities", error)
                        _uiState.update { 
                            it.copy(
                                isFacilitiesLoading = false,
                                errorMessage = getErrorMessage(error)
                            )
                        }
                    }
            } catch (e: Exception) {
                Log.e(TAG, "Exception while loading facilities", e)
                _uiState.update { 
                    it.copy(
                        isFacilitiesLoading = false,
                        errorMessage = getErrorMessage(e)
                    )
                }
            }
        }
    }
    
    /**
     * 시설물 새로고침
     */
    fun refreshFacilities() {
        val bbox = lastBbox ?: return
        lastBbox = null  // 강제 재조회
        loadFacilities(bbox)
    }
    
    /**
     * 레이어 가시성 토글
     */
    fun toggleLayer(layer: MapLayer, visible: Boolean) {
        _uiState.update { state ->
            state.copy(
                layerVisibility = when (layer) {
                    MapLayer.POLES -> state.layerVisibility.copy(poles = visible)
                    MapLayer.LINES -> state.layerVisibility.copy(lines = visible)
                    MapLayer.TRANSFORMERS -> state.layerVisibility.copy(transformers = visible)
                    MapLayer.ROADS -> state.layerVisibility.copy(roads = visible)
                    MapLayer.BUILDINGS -> state.layerVisibility.copy(buildings = visible)
                }
            )
        }
    }
    
    // ===== 설계 관리 =====
    
    /**
     * 설계 요청
     */
    fun submitDesign() {
        val state = _uiState.value
        
        val coordX = state.coordX.toDoubleOrNull()
        val coordY = state.coordY.toDoubleOrNull()
        
        if (coordX == null || coordY == null) {
            _uiState.update { it.copy(errorMessage = "올바른 좌표를 입력해주세요") }
            return
        }
        
        viewModelScope.launch {
            _uiState.update { it.copy(isDesignLoading = true, errorMessage = null) }
            
            val request = DesignRequest(
                coordX = coordX,
                coordY = coordY,
                phaseCode = state.phaseCode
            )
            
            try {
                createDesignUseCase(request)
                    .onSuccess { result ->
                        _uiState.update { 
                            it.copy(
                                isDesignLoading = false,
                                designResult = result,
                                selectedRouteIndex = 0
                            )
                        }
                    }
                    .onFailure { error ->
                        _uiState.update { 
                            it.copy(
                                isDesignLoading = false,
                                errorMessage = error.message ?: "설계 요청 실패"
                            )
                        }
                    }
            } catch (e: Exception) {
                _uiState.update { 
                    it.copy(
                        isDesignLoading = false,
                        errorMessage = getErrorMessage(e)
                    )
                }
            }
        }
    }
    
    /**
     * 경로 선택
     */
    fun selectRoute(index: Int) {
        _uiState.update { it.copy(selectedRouteIndex = index) }
    }
    
    /**
     * 설계 결과 초기화
     */
    fun clearDesignResult() {
        _uiState.update { it.copy(designResult = null, selectedRouteIndex = 0) }
    }
    
    // ===== 공통 =====
    
    /**
     * 에러 메시지 클리어
     */
    fun clearError() {
        _uiState.update { it.copy(errorMessage = null) }
    }
    
    /**
     * 에러 메시지 변환
     */
    private fun getErrorMessage(error: Throwable): String {
        return when {
            error.message?.contains("Unable to resolve host") == true -> 
                "서버에 연결할 수 없습니다.\n네트워크 연결을 확인하세요."
            error.message?.contains("timeout") == true ->
                "서버 응답 시간이 초과되었습니다.\n잠시 후 다시 시도하세요."
            error.message?.contains("Connection refused") == true ->
                "서버에 연결할 수 없습니다.\n서버가 실행 중인지 확인하세요."
            else -> error.message ?: "알 수 없는 오류가 발생했습니다."
        }
    }
}

/**
 * 메인 화면 UI 상태
 */
data class MainUiState(
    // 지도 상태
    val mapState: MapState = MapState(),
    val mapMoveRequest: Coordinate? = null,  // 지도 이동 요청
    
    // 좌표 입력
    val selectedCoord: Coordinate? = null,
    val coordX: String = "",
    val coordY: String = "",
    val phaseCode: PhaseCode = PhaseCode.SINGLE,
    
    // 시설물
    val showFacilities: Boolean = true,
    val facilities: FacilitiesData? = null,
    val layerVisibility: LayerVisibility = LayerVisibility(),
    val isFacilitiesLoading: Boolean = false,
    
    // 설계
    val designResult: DesignResult? = null,
    val selectedRouteIndex: Int = 0,
    val isDesignLoading: Boolean = false,
    
    // 공통
    val errorMessage: String? = null
) {
    val isValidInput: Boolean
        get() = coordX.toDoubleOrNull() != null && coordY.toDoubleOrNull() != null
    
    val hasDesignResult: Boolean
        get() = designResult != null
}

/**
 * 지도 상태 (위치, 줌)
 */
data class MapState(
    val centerLat: Double = CoordinateUtils.SeoulCityHall.LAT,
    val centerLng: Double = CoordinateUtils.SeoulCityHall.LNG,
    val zoom: Double = CoordinateUtils.DEFAULT_ZOOM
)

/**
 * 레이어 가시성 상태
 */
data class LayerVisibility(
    val poles: Boolean = true,
    val lines: Boolean = true,
    val transformers: Boolean = true,
    val roads: Boolean = false,
    val buildings: Boolean = false
)

/**
 * 지도 레이어 열거형
 */
enum class MapLayer {
    POLES, LINES, TRANSFORMERS, ROADS, BUILDINGS
}
