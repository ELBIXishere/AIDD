import { useState } from 'react'
import Button from '../common/Button'
import SavedRoutesPanel from './SavedRoutesPanel'

/**
 * 제어 패널 컴포넌트
 * - 좌표 입력
 * - 상(Phase) 선택
 * - 설계 실행 버튼
 * - 시설물 표시 (현재 화면 영역 기준)
 * - 저장된 경로 목록
 */
export default function ControlPanel({
  coord,
  phaseCode,
  loading,
  showFacilities,
  facilitiesLoading = false,
  savedRoutes = [],
  onCoordChange,
  onPhaseChange,
  onRunDesign,
  onClearCoord,
  onLoadFacilities,
  onToggleFacilities,
  onRefreshFacilities,
  onRemoveSavedRoute,
  onClearSavedRoutes,
}) {
  // 직접 입력 모드
  const [inputX, setInputX] = useState('')
  const [inputY, setInputY] = useState('')
  const [isManualInput, setIsManualInput] = useState(false)
  
  // 좌표 직접 입력 적용
  const handleApplyCoord = () => {
    const x = parseFloat(inputX)
    const y = parseFloat(inputY)
    
    if (!isNaN(x) && !isNaN(y)) {
      onCoordChange([x, y])
      setIsManualInput(false)
    }
  }
  
  // 테스트 좌표 예시
  const testCoords = [
    { name: '충주시 연수동 1', coord: [14242500.63, 4437638.69] },
    { name: '충주시 연수동 2', coord: [14242910.96, 4437665.32] },
    { name: '충주시 안림동', coord: [14243659.27, 4436489.88] },
  ]
  
  return (
    <div className="p-4 border-b border-slate-700 overflow-y-auto">
      <h2 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
        <svg className="w-4 h-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        설계 설정
      </h2>
      
      {/* 수용가 좌표 */}
      <div className="mb-4">
        <label className="block text-xs text-slate-400 mb-2">
          수용가 좌표 (EPSG:3857)
        </label>
        
        {/* 현재 좌표 표시 */}
        <div className="bg-bg-primary rounded-lg p-3 mb-2">
          {coord ? (
            <div className="font-mono text-sm">
              <div className="flex justify-between items-center mb-1">
                <span className="text-slate-500 text-xs">선택된 좌표</span>
                <button
                  onClick={onClearCoord}
                  className="text-xs text-red-400 hover:text-red-300 transition-colors"
                  title="좌표 선택 취소"
                >
                  ✕ 취소
                </button>
              </div>
              <div className="flex justify-between text-slate-300">
                <span className="text-slate-500">X:</span>
                <span>{coord[0].toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span className="text-slate-500">Y:</span>
                <span>{coord[1].toFixed(2)}</span>
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-500 text-center py-2">
              지도를 클릭하여 위치 선택
            </p>
          )}
        </div>
        
        {/* 직접 입력 토글 */}
        <button
          onClick={() => setIsManualInput(!isManualInput)}
          className="text-xs text-accent hover:text-accent-light transition-colors"
        >
          {isManualInput ? '취소' : '좌표 직접 입력'}
        </button>
        
        {/* 직접 입력 폼 */}
        {isManualInput && (
          <div className="mt-2 space-y-2">
            <div className="flex gap-2">
              <input
                type="number"
                value={inputX}
                onChange={(e) => setInputX(e.target.value)}
                placeholder="X 좌표"
                className="flex-1 bg-bg-primary border border-slate-600 rounded px-2 py-1.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-accent"
              />
              <input
                type="number"
                value={inputY}
                onChange={(e) => setInputY(e.target.value)}
                placeholder="Y 좌표"
                className="flex-1 bg-bg-primary border border-slate-600 rounded px-2 py-1.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-accent"
              />
            </div>
            <Button size="sm" variant="secondary" onClick={handleApplyCoord}>
              좌표 적용
            </Button>
          </div>
        )}
        
        {/* 테스트 좌표 */}
        <div className="mt-3">
          <label className="block text-xs text-slate-500 mb-1.5">테스트 좌표</label>
          <div className="flex flex-wrap gap-1">
            {testCoords.map((item, index) => (
              <button
                key={index}
                onClick={() => onCoordChange(item.coord)}
                className="px-2 py-1 text-xs bg-bg-primary hover:bg-bg-tertiary text-slate-400 hover:text-white rounded transition-colors"
              >
                {item.name}
              </button>
            ))}
          </div>
        </div>
      </div>
      
      {/* 상(Phase) 선택 */}
      <div className="mb-4">
        <label className="block text-xs text-slate-400 mb-2">
          신청 규격
        </label>
        <div className="flex gap-2">
          <label className={`
            flex-1 flex items-center justify-center gap-2 p-3 rounded-lg cursor-pointer transition-all
            ${phaseCode === '1' 
              ? 'bg-accent/20 border-2 border-accent text-accent' 
              : 'bg-bg-primary border-2 border-slate-600 text-slate-400 hover:border-slate-500'}
          `}>
            <input
              type="radio"
              name="phase"
              value="1"
              checked={phaseCode === '1'}
              onChange={(e) => onPhaseChange(e.target.value)}
              className="sr-only"
            />
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span className="text-sm font-medium">단상</span>
          </label>
          
          <label className={`
            flex-1 flex items-center justify-center gap-2 p-3 rounded-lg cursor-pointer transition-all
            ${phaseCode === '3' 
              ? 'bg-accent/20 border-2 border-accent text-accent' 
              : 'bg-bg-primary border-2 border-slate-600 text-slate-400 hover:border-slate-500'}
          `}>
            <input
              type="radio"
              name="phase"
              value="3"
              checked={phaseCode === '3'}
              onChange={(e) => onPhaseChange(e.target.value)}
              className="sr-only"
            />
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                d="M13 10V3L4 14h7v7l9-11h-7z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                d="M17 10V3L8 14h7v7l9-11h-7z" opacity="0.5" />
            </svg>
            <span className="text-sm font-medium">3상</span>
          </label>
        </div>
      </div>
      
      {/* 실행 버튼 */}
      <Button
        onClick={onRunDesign}
        loading={loading}
        disabled={!coord}
        className="w-full"
        size="lg"
      >
        {loading ? '설계 분석 중...' : '설계 실행'}
      </Button>
      
      {!coord && (
        <p className="text-xs text-slate-500 text-center mt-2">
          지도에서 수용가 위치를 먼저 선택하세요
        </p>
      )}
      
      {/* 시설물 표시 */}
      <div className="mt-4 pt-4 border-t border-slate-700">
        <div className="flex items-center justify-between mb-2">
          <label className="block text-xs text-slate-400">
            시설물 표시
          </label>
          <div className="flex items-center gap-2">
            {/* 새로고침 버튼 */}
            {showFacilities && (
              <button
                onClick={onRefreshFacilities}
                disabled={facilitiesLoading}
                className={`
                  p-1 rounded transition-colors
                  ${facilitiesLoading 
                    ? 'text-slate-600 cursor-not-allowed' 
                    : 'text-slate-400 hover:text-accent hover:bg-bg-tertiary'}
                `}
                title="현재 화면 영역으로 새로고침"
              >
                <svg className={`w-4 h-4 ${facilitiesLoading ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
            )}
            
            {/* 토글 스위치 */}
            <button
              onClick={onToggleFacilities}
              disabled={facilitiesLoading}
              className={`
                relative w-10 h-5 rounded-full transition-colors
                ${showFacilities ? 'bg-accent' : 'bg-slate-600'}
                ${facilitiesLoading ? 'opacity-50 cursor-wait' : ''}
              `}
            >
              <span className={`
                absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform
                ${showFacilities ? 'translate-x-5' : 'translate-x-0'}
              `} />
            </button>
          </div>
        </div>
        <p className="text-xs text-slate-500">
          현재 화면 영역의 전주, 전선, 변압기, 도로, 건물 등을 표시합니다
        </p>
        {facilitiesLoading && (
          <div className="flex items-center gap-2 mt-2 text-amber-400 text-xs">
            <div className="w-3 h-3 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
            <span>시설물 로드 중...</span>
          </div>
        )}
        {showFacilities && !facilitiesLoading && (
          <p className="text-xs text-green-400 mt-2">
            ✓ 시설물 표시 중 (지도를 이동 후 새로고침 버튼 클릭)
          </p>
        )}
      </div>
      
      {/* 저장된 경로 목록 */}
      <SavedRoutesPanel
        savedRoutes={savedRoutes}
        onRemove={onRemoveSavedRoute}
        onClearAll={onClearSavedRoutes}
      />
    </div>
  )
}
