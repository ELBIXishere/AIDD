import { useState } from 'react'
import { downloadSavedRoutesCSV } from '../../utils/csvExport'

/**
 * 저장된 경로 목록 패널 컴포넌트
 * - 저장된 경로 목록 표시
 * - 개별/전체 삭제
 * - CSV 추출
 */
export default function SavedRoutesPanel({
  savedRoutes,
  onRemove,
  onClearAll
}) {
  // 패널 펼침/접힘 상태
  const [isExpanded, setIsExpanded] = useState(true)
  
  // 비용 포맷
  const formatCost = (cost) => {
    if (!cost) return '-'
    return new Intl.NumberFormat('ko-KR').format(cost) + '원'
  }
  
  // 거리 포맷
  const formatDistance = (distance) => {
    if (!distance) return '-'
    return `${distance.toFixed(1)}m`
  }
  
  // 날짜 포맷
  const formatDate = (isoString) => {
    const date = new Date(isoString)
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    return `${month}/${day} ${hours}:${minutes}`
  }
  
  // CSV 추출 핸들러
  const handleExportCSV = () => {
    if (savedRoutes.length === 0) return
    
    const success = downloadSavedRoutesCSV(savedRoutes)
    if (!success) {
      console.error('CSV 추출 실패')
    }
  }
  
  // 저장된 경로가 없을 때
  if (savedRoutes.length === 0) {
    return (
      <div className="border-t border-slate-700 pt-4 mt-4">
        <div className="flex items-center gap-2 text-slate-400 mb-2">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
              d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
          </svg>
          <span className="text-sm font-medium">저장 목록</span>
          <span className="text-xs text-slate-500">(0)</span>
        </div>
        <p className="text-xs text-slate-500">
          설계 결과에서 경로를 저장하면 여기에 표시됩니다.
        </p>
      </div>
    )
  }
  
  return (
    <div className="border-t border-slate-700 pt-4 mt-4">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-3">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-2 text-slate-300 hover:text-white transition-colors"
        >
          <svg 
            className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-90' : ''}`} 
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
              d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
          </svg>
          <span className="text-sm font-medium">저장 목록</span>
          <span className="text-xs bg-accent/20 text-accent px-1.5 py-0.5 rounded-full">
            {savedRoutes.length}
          </span>
        </button>
      </div>
      
      {/* 펼침 상태일 때만 내용 표시 */}
      {isExpanded && (
        <>
          {/* 저장된 경로 목록 */}
          <div className="space-y-2 max-h-48 overflow-y-auto mb-3">
            {savedRoutes.map((item) => (
              <div 
                key={item.id}
                className="bg-bg-primary rounded-lg p-2 text-xs"
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span className={`
                      px-1.5 py-0.5 rounded text-[10px] font-medium
                      ${item.requestSpec === '3상' 
                        ? 'bg-amber-500/20 text-amber-400' 
                        : 'bg-blue-500/20 text-blue-400'}
                    `}>
                      {item.requestSpec}
                    </span>
                    <span className="text-slate-500">{formatDate(item.savedAt)}</span>
                  </div>
                  <button
                    onClick={() => onRemove(item.id)}
                    className="text-slate-500 hover:text-red-400 transition-colors p-1"
                    title="삭제"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                <div className="flex items-center gap-3 text-slate-400">
                  <span>거리: {formatDistance(item.route.total_distance)}</span>
                  <span>전주: {item.route.new_poles_count || 0}개</span>
                </div>
                <div className="text-slate-300 mt-1">
                  비용: {formatCost(item.route.total_cost)}
                </div>
              </div>
            ))}
          </div>
          
          {/* 버튼 그룹 */}
          <div className="flex gap-2">
            {/* CSV 추출 버튼 */}
            <button
              onClick={handleExportCSV}
              className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 
                       text-xs font-medium text-white bg-accent hover:bg-accent/90 
                       rounded-lg transition-colors"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              CSV 추출
            </button>
            
            {/* 전체 삭제 버튼 */}
            <button
              onClick={onClearAll}
              className="flex items-center justify-center gap-1.5 px-3 py-2 
                       text-xs font-medium text-slate-400 bg-slate-700 hover:bg-slate-600 
                       rounded-lg transition-colors"
              title="저장 목록 전체 삭제"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </>
      )}
    </div>
  )
}
