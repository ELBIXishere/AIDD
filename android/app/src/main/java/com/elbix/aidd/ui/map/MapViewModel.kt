package com.elbix.aidd.ui.map

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.elbix.aidd.domain.model.BoundingBox
import com.elbix.aidd.domain.model.FacilitiesData
import com.elbix.aidd.domain.usecase.GetFacilitiesUseCase
import com.elbix.aidd.ui.main.LayerVisibility
import com.elbix.aidd.ui.main.MapLayer
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * 지도 화면 ViewModel
 * - 시설물 데이터 관리
 * - 레이어 가시성 관리
 */
@HiltViewModel
class MapViewModel @Inject constructor(
    private val getFacilitiesUseCase: GetFacilitiesUseCase
) : ViewModel() {
    
    companion object {
        private const val TAG = "MapViewModel"
    }
    
    private val _uiState = MutableStateFlow(MapUiState())
    val uiState: StateFlow<MapUiState> = _uiState.asStateFlow()
    
    // 현재 조회된 영역 저장 (중복 조회 방지)
    private var lastBbox: BoundingBox? = null
    
    // 기본 BBox (서울 시청 주변, EPSG:3857)
    private val defaultBbox = BoundingBox(
        minX = 14128000.0,
        minY = 4510000.0,
        maxX = 14138000.0,
        maxY = 4520000.0
    )
    
    /**
     * 시설물 데이터 조회
     */
    fun loadFacilities(bbox: BoundingBox) {
        // 동일 영역 중복 조회 방지
        if (bbox == lastBbox) return
        lastBbox = bbox
        
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, errorMessage = null) }
            
            try {
                Log.d(TAG, "Loading facilities for bbox: $bbox")
                
                getFacilitiesUseCase(bbox)
                    .onSuccess { facilities ->
                        Log.d(TAG, "Facilities loaded: poles=${facilities.poles.size}")
                        _uiState.update { 
                            it.copy(
                                isLoading = false,
                                facilities = facilities
                            )
                        }
                    }
                    .onFailure { error ->
                        Log.e(TAG, "Failed to load facilities", error)
                        _uiState.update { 
                            it.copy(
                                isLoading = false,
                                errorMessage = getErrorMessage(error)
                            )
                        }
                    }
            } catch (e: Exception) {
                Log.e(TAG, "Exception while loading facilities", e)
                _uiState.update { 
                    it.copy(
                        isLoading = false,
                        errorMessage = getErrorMessage(e)
                    )
                }
            }
        }
    }
    
    /**
     * 시설물 새로고침 (수동)
     */
    fun refreshFacilities() {
        val bbox = lastBbox ?: defaultBbox
        lastBbox = null  // 강제 재조회
        loadFacilities(bbox)
    }
    
    /**
     * 기본 영역으로 시설물 조회
     */
    fun loadDefaultArea() {
        loadFacilities(defaultBbox)
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
                "서버 응답 시간이 초과되었습니다."
            error.message?.contains("Connection refused") == true ->
                "서버가 응답하지 않습니다.\n서버 상태를 확인하세요."
            else -> error.message ?: "알 수 없는 오류가 발생했습니다."
        }
    }
}

/**
 * 지도 화면 UI 상태
 */
data class MapUiState(
    val isLoading: Boolean = false,
    val facilities: FacilitiesData? = null,
    val layerVisibility: LayerVisibility = LayerVisibility(),
    val errorMessage: String? = null
)
