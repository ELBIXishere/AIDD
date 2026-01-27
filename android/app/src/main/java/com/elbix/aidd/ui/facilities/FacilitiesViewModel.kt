package com.elbix.aidd.ui.facilities

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
 * 시설물 조회 화면 ViewModel
 */
@HiltViewModel
class FacilitiesViewModel @Inject constructor(
    private val getFacilitiesUseCase: GetFacilitiesUseCase
) : ViewModel() {
    
    private val _uiState = MutableStateFlow(FacilitiesUiState())
    val uiState: StateFlow<FacilitiesUiState> = _uiState.asStateFlow()
    
    private var lastBbox: BoundingBox? = null
    
    /**
     * 시설물 조회
     */
    fun loadFacilities(bbox: BoundingBox) {
        // 중복 조회 방지
        if (bbox == lastBbox && _uiState.value.facilities != null) return
        lastBbox = bbox
        
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, errorMessage = null) }
            
            getFacilitiesUseCase(bbox)
                .onSuccess { facilities ->
                    _uiState.update { 
                        it.copy(
                            isLoading = false,
                            facilities = facilities,
                            facilitiesCount = FacilitiesCount(
                                poles = facilities.poles.size,
                                lines = facilities.lines.size,
                                transformers = facilities.transformers.size,
                                roads = facilities.roads.size,
                                buildings = facilities.buildings.size
                            )
                        )
                    }
                }
                .onFailure { error ->
                    _uiState.update { 
                        it.copy(
                            isLoading = false,
                            errorMessage = error.message ?: "시설물 조회 실패"
                        )
                    }
                }
        }
    }
    
    /**
     * 새로고침
     */
    fun refresh() {
        lastBbox?.let { bbox ->
            lastBbox = null
            loadFacilities(bbox)
        }
    }
    
    /**
     * 레이어 토글
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
     * 에러 클리어
     */
    fun clearError() {
        _uiState.update { it.copy(errorMessage = null) }
    }
}

/**
 * 시설물 화면 UI 상태
 */
data class FacilitiesUiState(
    val isLoading: Boolean = false,
    val facilities: FacilitiesData? = null,
    val layerVisibility: LayerVisibility = LayerVisibility(
        poles = true,
        lines = true,
        transformers = true,
        roads = false,
        buildings = false
    ),
    val facilitiesCount: FacilitiesCount = FacilitiesCount(),
    val errorMessage: String? = null
) {
    /**
     * 활성 레이어 수
     */
    val activeLayerCount: Int
        get() = listOf(
            layerVisibility.poles,
            layerVisibility.lines,
            layerVisibility.transformers,
            layerVisibility.roads,
            layerVisibility.buildings
        ).count { it }
}

/**
 * 시설물 개수 데이터
 */
data class FacilitiesCount(
    val poles: Int = 0,
    val lines: Int = 0,
    val transformers: Int = 0,
    val roads: Int = 0,
    val buildings: Int = 0
) {
    val total: Int get() = poles + lines + transformers + roads + buildings
}
