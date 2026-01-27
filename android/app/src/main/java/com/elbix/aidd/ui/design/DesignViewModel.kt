package com.elbix.aidd.ui.design

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.elbix.aidd.domain.model.Coordinate
import com.elbix.aidd.domain.model.DesignRequest
import com.elbix.aidd.domain.model.DesignResult
import com.elbix.aidd.domain.model.PhaseCode
import com.elbix.aidd.domain.usecase.CreateDesignUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * 배전 설계 화면 ViewModel
 * - 좌표 입력 관리
 * - 설계 요청 처리
 * - 결과 상태 관리
 */
@HiltViewModel
class DesignViewModel @Inject constructor(
    private val createDesignUseCase: CreateDesignUseCase
) : ViewModel() {
    
    private val _uiState = MutableStateFlow(DesignUiState())
    val uiState: StateFlow<DesignUiState> = _uiState.asStateFlow()
    
    /**
     * 좌표 문자열로 설정 ("x,y" 형식)
     */
    fun setCoordinate(coordString: String) {
        try {
            val parts = coordString.split(",")
            if (parts.size == 2) {
                _uiState.update { 
                    it.copy(
                        coordX = parts[0].trim(),
                        coordY = parts[1].trim()
                    )
                }
            }
        } catch (e: Exception) {
            // 파싱 실패 시 무시
        }
    }
    
    /**
     * X 좌표 업데이트
     */
    fun updateCoordX(value: String) {
        _uiState.update { it.copy(coordX = value) }
    }
    
    /**
     * Y 좌표 업데이트
     */
    fun updateCoordY(value: String) {
        _uiState.update { it.copy(coordY = value) }
    }
    
    /**
     * 상 코드 업데이트
     */
    fun updatePhaseCode(phaseCode: PhaseCode) {
        _uiState.update { it.copy(phaseCode = phaseCode) }
    }
    
    /**
     * 설계 요청 제출
     */
    fun submitDesign() {
        val state = _uiState.value
        
        // 입력 유효성 검사
        val coordX = state.coordX.toDoubleOrNull()
        val coordY = state.coordY.toDoubleOrNull()
        
        if (coordX == null || coordY == null) {
            _uiState.update { it.copy(errorMessage = "올바른 좌표를 입력해주세요") }
            return
        }
        
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, errorMessage = null) }
            
            val request = DesignRequest(
                coordX = coordX,
                coordY = coordY,
                phaseCode = state.phaseCode
            )
            
            createDesignUseCase(request)
                .onSuccess { result ->
                    _uiState.update { 
                        it.copy(
                            isLoading = false,
                            result = result,
                            selectedRouteIndex = 0
                        )
                    }
                }
                .onFailure { error ->
                    _uiState.update { 
                        it.copy(
                            isLoading = false,
                            errorMessage = error.message ?: "설계 요청 실패"
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
     * 상태 초기화
     */
    fun reset() {
        _uiState.update { 
            DesignUiState(
                coordX = it.coordX,
                coordY = it.coordY,
                phaseCode = it.phaseCode
            )
        }
    }
    
    /**
     * 에러 메시지 클리어
     */
    fun clearError() {
        _uiState.update { it.copy(errorMessage = null) }
    }
}

/**
 * 설계 화면 UI 상태
 */
data class DesignUiState(
    val coordX: String = "",
    val coordY: String = "",
    val phaseCode: PhaseCode = PhaseCode.SINGLE,
    val isLoading: Boolean = false,
    val result: DesignResult? = null,
    val selectedRouteIndex: Int = 0,
    val errorMessage: String? = null
) {
    /**
     * 입력 유효성 검사
     */
    val isValidInput: Boolean
        get() = coordX.toDoubleOrNull() != null && coordY.toDoubleOrNull() != null
}
