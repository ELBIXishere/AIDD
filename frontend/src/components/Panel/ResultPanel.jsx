import Loading from '../common/Loading'
import { downloadFullCSV } from '../../utils/csvExport'

/**
 * 결과 패널 컴포넌트
 * - 설계 결과 경로 목록
 * - 경로별 상세 정보
 * - CSV 다운로드 기능
 */
export default function ResultPanel({
  result,
  error,
  selectedIndex,
  onSelectRoute,
  onSaveRoute,   // 경로 저장 핸들러
  requestSpec,   // 요청 규격 (단상/3상)
}) {
  // 에러 상태
  if (error) {
    return (
      <div className="flex-1 p-4 overflow-auto">
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-4">
          <div className="flex items-center gap-2 text-red-400 mb-2">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="font-medium">오류 발생</span>
          </div>
          <p className="text-sm text-red-300">{error}</p>
        </div>
      </div>
    )
  }
  
  // 결과 없음
  if (!result) {
    return (
      <div className="flex-1 p-4 flex items-center justify-center">
        <div className="text-center text-slate-500">
          <svg className="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} 
              d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
          </svg>
          <p className="text-sm">설계 결과가 여기에 표시됩니다</p>
        </div>
      </div>
    )
  }
  
  // 경로 없음
  if (result.status === 'no_route' || !result.routes || result.routes.length === 0) {
    return (
      <div className="flex-1 p-4 overflow-auto">
        <div className="bg-amber-900/30 border border-amber-700 rounded-lg p-4">
          <div className="flex items-center gap-2 text-amber-400 mb-2">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span className="font-medium">경로 없음</span>
          </div>
          <p className="text-sm text-amber-300">
            조건에 맞는 경로를 찾을 수 없습니다.
          </p>
          <p className="text-xs text-amber-400/70 mt-2">
            • 400m 범위 내 후보 전주가 없거나<br/>
            • 모든 경로가 전선 교차 등 제약 조건에 위배됩니다.
          </p>
        </div>
      </div>
    )
  }
  
  /**
   * CSV 다운로드 핸들러
   */
  const handleDownloadCSV = () => {
    const success = downloadFullCSV(result)
    if (!success) {
      console.error('CSV 다운로드 실패')
    }
  }
  
  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* 헤더 */}
      <div className="p-4 border-b border-slate-700">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <svg className="w-4 h-4 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            설계 결과
          </h2>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">
              {result.routes.length}개 경로
            </span>
            {/* CSV 다운로드 버튼 */}
            <button
              onClick={handleDownloadCSV}
              className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium
                       text-slate-300 bg-slate-700 hover:bg-slate-600 
                       rounded-lg transition-colors"
              title="설계 결과를 CSV 파일로 다운로드"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              CSV
            </button>
          </div>
        </div>
        
        {/* 요청 규격 표시 */}
        {(requestSpec || result.request_spec) && (
          <div className="mt-2 flex items-center gap-2">
            <span className={`
              px-2 py-0.5 rounded text-xs font-medium
              ${(requestSpec || result.request_spec) === '3상' 
                ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' 
                : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'}
            `}>
              {requestSpec || result.request_spec}
            </span>
            <span className={`
              px-2 py-0.5 rounded text-xs font-medium
              ${(requestSpec || result.request_spec) === '3상' 
                ? 'bg-red-500/20 text-red-400 border border-red-500/30' 
                : 'bg-green-500/20 text-green-400 border border-green-500/30'}
            `}>
              {(requestSpec || result.request_spec) === '3상' ? '고압' : '저압'}
            </span>
          </div>
        )}
        
        {/* 처리 시간 */}
        {result.processing_time_ms && (
          <div className="mt-2 text-xs text-slate-500">
            처리 시간: {result.processing_time_ms}ms
          </div>
        )}
      </div>
      
      {/* 경로 목록 */}
      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {result.routes.map((route, index) => (
          <RouteCard
            key={index}
            route={route}
            index={index}
            isSelected={index === selectedIndex}
            onClick={() => onSelectRoute(index)}
            onSave={() => onSaveRoute(route)}
          />
        ))}
      </div>
    </div>
  )
}

/**
 * 개별 경로 카드 컴포넌트
 */
function RouteCard({ route, index, isSelected, onClick, onSave }) {
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
  
  return (
    <button
      onClick={onClick}
      className={`
        w-full text-left p-3 rounded-lg transition-all
        ${isSelected 
          ? 'bg-accent/20 border-2 border-accent' 
          : 'bg-bg-primary border-2 border-transparent hover:border-slate-600'}
      `}
    >
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className={`
            w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold
            ${index === 0 ? 'bg-green-500 text-white' : 'bg-slate-600 text-slate-300'}
          `}>
            {route.rank || index + 1}
          </span>
          <span className="text-sm font-medium text-slate-200">
            {index === 0 ? '최적 경로' : `경로 ${index + 1}`}
          </span>
        </div>
        
        <div className="flex items-center gap-2">
          {/* 저장 버튼 */}
          <button
            onClick={(e) => {
              e.stopPropagation()  // 카드 클릭 이벤트 전파 방지
              onSave()
            }}
            className="flex items-center gap-1 px-2 py-1 text-xs font-medium
                     text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20 
                     border border-emerald-500/30 rounded transition-colors"
            title="이 경로를 저장 목록에 추가"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
            </svg>
            저장
          </button>
          
          {isSelected && (
            <svg className="w-4 h-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          )}
        </div>
      </div>
      
      {/* 상세 정보 */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="bg-bg-secondary rounded p-2">
          <div className="text-slate-500 mb-0.5">신설 전주</div>
          <div className="text-slate-200 font-medium">
            {route.new_poles_count || 0}개
          </div>
        </div>
        
        <div className="bg-bg-secondary rounded p-2">
          <div className="text-slate-500 mb-0.5">총 거리</div>
          <div className="text-slate-200 font-medium">
            {formatDistance(route.total_distance)}
          </div>
        </div>
        
        <div className="bg-bg-secondary rounded p-2">
          <div className="text-slate-500 mb-0.5">비용 지수</div>
          <div className="text-slate-200 font-medium">
            {route.cost_index?.toLocaleString() || '-'}
          </div>
        </div>
        
        <div className="bg-bg-secondary rounded p-2">
          <div className="text-slate-500 mb-0.5">예상 비용</div>
          <div className="text-slate-200 font-medium text-xs">
            {formatCost(route.total_cost)}
          </div>
        </div>
      </div>
      
      {/* 기설 전주 정보 */}
      {route.start_pole_id && (
        <div className="mt-2 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <span>기설전주:</span>
            <span className="text-slate-400 font-mono">{route.start_pole_id}</span>
            {/* 전압/상 정보 배지 */}
            {route.source_voltage_type && (
              <span className={`
                px-1.5 py-0.5 rounded text-[10px] font-medium
                ${route.source_voltage_type === 'HV' 
                  ? 'bg-red-500/20 text-red-400' 
                  : 'bg-green-500/20 text-green-400'}
              `}>
                {route.source_voltage_type === 'HV' ? '고압' : '저압'}
              </span>
            )}
            {route.source_phase_type && (
              <span className={`
                px-1.5 py-0.5 rounded text-[10px] font-medium
                ${route.source_phase_type === '3' 
                  ? 'bg-amber-500/20 text-amber-400' 
                  : 'bg-blue-500/20 text-blue-400'}
              `}>
                {route.source_phase_type === '3' ? '3상' : '단상'}
              </span>
            )}
          </div>
        </div>
      )}
      
      {/* 전압 강하 정보 */}
      {route.voltage_drop && (
        <div className={`
          mt-2 flex items-center gap-2 text-xs rounded px-2 py-1
          ${route.voltage_drop.is_acceptable 
            ? 'bg-green-900/20 text-green-400' 
            : 'bg-red-900/20 text-red-400'}
        `}>
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
              d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <span>
            전압강하: {route.voltage_drop.voltage_drop_percent?.toFixed(2)}%
            {!route.voltage_drop.is_acceptable && ' (초과!)'}
          </span>
        </div>
      )}
      
      {/* 비용 상세 (확장 시) */}
      {isSelected && route.cost_breakdown && (
        <div className="mt-3 pt-3 border-t border-slate-700">
          <div className="text-xs text-slate-400 mb-2">비용 상세</div>
          <div className="space-y-1 text-xs">
            {route.cost_breakdown.pole_cost > 0 && (
              <div className="flex justify-between">
                <span className="text-slate-500">전주 비용</span>
                <span className="text-slate-300">{formatCost(route.cost_breakdown.pole_cost)}</span>
              </div>
            )}
            {route.cost_breakdown.wire_cost > 0 && (
              <div className="flex justify-between">
                <span className="text-slate-500">전선 비용</span>
                <span className="text-slate-300">{formatCost(route.cost_breakdown.wire_cost)}</span>
              </div>
            )}
            {route.cost_breakdown.labor_cost > 0 && (
              <div className="flex justify-between">
                <span className="text-slate-500">인건비</span>
                <span className="text-slate-300">{formatCost(route.cost_breakdown.labor_cost)}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </button>
  )
}
