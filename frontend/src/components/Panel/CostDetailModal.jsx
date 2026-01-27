import { useMemo } from 'react'

/**
 * 공사비 상세 모달 컴포넌트
 * - 재료비/인건비/경비 파이차트
 * - 항목별 수량 및 단가 테이블
 */
export default function CostDetailModal({ route, isOpen, onClose }) {
  if (!isOpen || !route) return null
  
  const detailedCost = route.detailed_cost
  
  // 비용 데이터 가공
  const costData = useMemo(() => {
    if (!detailedCost) return null
    
    const materialTotal = detailedCost.material?.total || 0
    const laborTotal = detailedCost.labor?.total || 0
    const overheadTotal = detailedCost.overhead_cost || 0
    const profitTotal = detailedCost.profit_cost || 0
    const total = detailedCost.total || (materialTotal + laborTotal + overheadTotal + profitTotal)
    
    return {
      material: materialTotal,
      labor: laborTotal,
      overhead: overheadTotal,
      profit: profitTotal,
      total,
      percentages: {
        material: total > 0 ? (materialTotal / total * 100).toFixed(1) : 0,
        labor: total > 0 ? (laborTotal / total * 100).toFixed(1) : 0,
        overhead: total > 0 ? (overheadTotal / total * 100).toFixed(1) : 0,
        profit: total > 0 ? (profitTotal / total * 100).toFixed(1) : 0,
      }
    }
  }, [detailedCost])
  
  // 비용 포맷
  const formatCost = (cost) => {
    if (!cost) return '-'
    return new Intl.NumberFormat('ko-KR').format(cost) + '원'
  }
  
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-bg-secondary rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
        {/* 헤더 */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <h2 className="text-lg font-semibold text-slate-200">
            공사비 상세 분석
          </h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        {/* 본문 */}
        <div className="p-4 overflow-y-auto max-h-[calc(90vh-60px)]">
          {!detailedCost ? (
            <div className="text-center text-slate-500 py-8">
              상세 비용 정보가 없습니다.
            </div>
          ) : (
            <div className="space-y-6">
              {/* 요약 카드 */}
              <div className="bg-bg-tertiary rounded-lg p-4">
                <div className="text-center mb-4">
                  <div className="text-sm text-slate-400">총 공사비</div>
                  <div className="text-2xl font-bold text-accent">
                    {formatCost(costData?.total)}
                  </div>
                </div>
                
                {/* 비용 비율 바 */}
                <div className="h-8 rounded-lg overflow-hidden flex">
                  <div 
                    className="bg-blue-500 flex items-center justify-center text-xs text-white font-medium"
                    style={{ width: `${costData?.percentages.material}%` }}
                    title={`재료비: ${formatCost(costData?.material)}`}
                  >
                    {costData?.percentages.material > 15 && '재료비'}
                  </div>
                  <div 
                    className="bg-green-500 flex items-center justify-center text-xs text-white font-medium"
                    style={{ width: `${costData?.percentages.labor}%` }}
                    title={`인건비: ${formatCost(costData?.labor)}`}
                  >
                    {costData?.percentages.labor > 15 && '인건비'}
                  </div>
                  <div 
                    className="bg-amber-500 flex items-center justify-center text-xs text-white font-medium"
                    style={{ width: `${costData?.percentages.overhead}%` }}
                    title={`경비: ${formatCost(costData?.overhead)}`}
                  >
                    {costData?.percentages.overhead > 10 && '경비'}
                  </div>
                  <div 
                    className="bg-purple-500 flex items-center justify-center text-xs text-white font-medium"
                    style={{ width: `${costData?.percentages.profit}%` }}
                    title={`이윤: ${formatCost(costData?.profit)}`}
                  >
                    {costData?.percentages.profit > 10 && '이윤'}
                  </div>
                </div>
                
                {/* 범례 */}
                <div className="flex flex-wrap justify-center gap-4 mt-3 text-xs">
                  <div className="flex items-center gap-1">
                    <div className="w-3 h-3 rounded bg-blue-500" />
                    <span className="text-slate-400">재료비 ({costData?.percentages.material}%)</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="w-3 h-3 rounded bg-green-500" />
                    <span className="text-slate-400">인건비 ({costData?.percentages.labor}%)</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="w-3 h-3 rounded bg-amber-500" />
                    <span className="text-slate-400">경비 ({costData?.percentages.overhead}%)</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="w-3 h-3 rounded bg-purple-500" />
                    <span className="text-slate-400">이윤 ({costData?.percentages.profit}%)</span>
                  </div>
                </div>
              </div>
              
              {/* 재료비 상세 테이블 */}
              <div>
                <h3 className="text-sm font-medium text-blue-400 mb-2 flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-blue-500" />
                  재료비 상세
                </h3>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-slate-400 text-xs border-b border-slate-700">
                      <th className="text-left py-2">항목</th>
                      <th className="text-right py-2">수량</th>
                      <th className="text-right py-2">단가</th>
                      <th className="text-right py-2">금액</th>
                    </tr>
                  </thead>
                  <tbody className="text-slate-300">
                    {detailedCost.material?.pole?.count > 0 && (
                      <tr className="border-b border-slate-700/50">
                        <td className="py-2">전주 ({detailedCost.material.pole.spec})</td>
                        <td className="text-right py-2">{detailedCost.material.pole.count}본</td>
                        <td className="text-right py-2">{formatCost(detailedCost.material.pole.unit_cost)}</td>
                        <td className="text-right py-2">{formatCost(detailedCost.material.pole.cost)}</td>
                      </tr>
                    )}
                    {detailedCost.material?.wire?.cost > 0 && (
                      <tr className="border-b border-slate-700/50">
                        <td className="py-2">전선 ({detailedCost.material.wire.spec})</td>
                        <td className="text-right py-2">{detailedCost.material.wire.length?.toFixed(1)}m</td>
                        <td className="text-right py-2">{formatCost(detailedCost.material.wire.unit_cost)}/m</td>
                        <td className="text-right py-2">{formatCost(detailedCost.material.wire.cost)}</td>
                      </tr>
                    )}
                    {detailedCost.material?.insulator?.count > 0 && (
                      <tr className="border-b border-slate-700/50">
                        <td className="py-2">애자</td>
                        <td className="text-right py-2">{detailedCost.material.insulator.count}개</td>
                        <td className="text-right py-2">-</td>
                        <td className="text-right py-2">{formatCost(detailedCost.material.insulator.cost)}</td>
                      </tr>
                    )}
                    {detailedCost.material?.arm_tie?.count > 0 && (
                      <tr className="border-b border-slate-700/50">
                        <td className="py-2">완금</td>
                        <td className="text-right py-2">{detailedCost.material.arm_tie.count}개</td>
                        <td className="text-right py-2">-</td>
                        <td className="text-right py-2">{formatCost(detailedCost.material.arm_tie.cost)}</td>
                      </tr>
                    )}
                    {detailedCost.material?.clamp?.count > 0 && (
                      <tr className="border-b border-slate-700/50">
                        <td className="py-2">클램프</td>
                        <td className="text-right py-2">{detailedCost.material.clamp.count}개</td>
                        <td className="text-right py-2">-</td>
                        <td className="text-right py-2">{formatCost(detailedCost.material.clamp.cost)}</td>
                      </tr>
                    )}
                    {detailedCost.material?.connector?.count > 0 && (
                      <tr className="border-b border-slate-700/50">
                        <td className="py-2">접속자재</td>
                        <td className="text-right py-2">{detailedCost.material.connector.count}개</td>
                        <td className="text-right py-2">-</td>
                        <td className="text-right py-2">{formatCost(detailedCost.material.connector.cost)}</td>
                      </tr>
                    )}
                    <tr className="font-medium">
                      <td className="py-2" colSpan="3">재료비 소계</td>
                      <td className="text-right py-2 text-blue-400">{formatCost(detailedCost.material?.total)}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              
              {/* 인건비 상세 테이블 */}
              <div>
                <h3 className="text-sm font-medium text-green-400 mb-2 flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-green-500" />
                  인건비 상세
                </h3>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-slate-400 text-xs border-b border-slate-700">
                      <th className="text-left py-2">항목</th>
                      <th className="text-right py-2">수량</th>
                      <th className="text-right py-2">단가</th>
                      <th className="text-right py-2">금액</th>
                    </tr>
                  </thead>
                  <tbody className="text-slate-300">
                    <tr className="border-b border-slate-700/50">
                      <td className="py-2">기본 노무비</td>
                      <td className="text-right py-2">1식</td>
                      <td className="text-right py-2">-</td>
                      <td className="text-right py-2">{formatCost(detailedCost.labor?.base)}</td>
                    </tr>
                    {detailedCost.labor?.pole_install?.count > 0 && (
                      <tr className="border-b border-slate-700/50">
                        <td className="py-2">전주 설치</td>
                        <td className="text-right py-2">{detailedCost.labor.pole_install.count}본</td>
                        <td className="text-right py-2">{formatCost(detailedCost.labor.pole_install.unit_cost)}/본</td>
                        <td className="text-right py-2">{formatCost(detailedCost.labor.pole_install.cost)}</td>
                      </tr>
                    )}
                    {detailedCost.labor?.wire_stretch?.cost > 0 && (
                      <tr className="border-b border-slate-700/50">
                        <td className="py-2">전선 가선</td>
                        <td className="text-right py-2">{detailedCost.labor.wire_stretch.length?.toFixed(1)}m</td>
                        <td className="text-right py-2">{formatCost(detailedCost.labor.wire_stretch.unit_cost)}/m</td>
                        <td className="text-right py-2">{formatCost(detailedCost.labor.wire_stretch.cost)}</td>
                      </tr>
                    )}
                    {detailedCost.labor?.insulator_install?.count > 0 && (
                      <tr className="border-b border-slate-700/50">
                        <td className="py-2">애자 설치</td>
                        <td className="text-right py-2">{detailedCost.labor.insulator_install.count}개</td>
                        <td className="text-right py-2">{formatCost(detailedCost.labor.insulator_install.unit_cost)}/개</td>
                        <td className="text-right py-2">{formatCost(detailedCost.labor.insulator_install.cost)}</td>
                      </tr>
                    )}
                    <tr className="font-medium">
                      <td className="py-2" colSpan="3">인건비 소계</td>
                      <td className="text-right py-2 text-green-400">{formatCost(detailedCost.labor?.total)}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              
              {/* 경비/이윤 */}
              <div>
                <h3 className="text-sm font-medium text-amber-400 mb-2">경비 및 이윤</h3>
                <table className="w-full text-sm">
                  <tbody className="text-slate-300">
                    <tr className="border-b border-slate-700/50">
                      <td className="py-2">경비 ({(detailedCost.overhead_rate * 100).toFixed(0)}%)</td>
                      <td className="text-right py-2">{formatCost(detailedCost.overhead_cost)}</td>
                    </tr>
                    <tr className="border-b border-slate-700/50">
                      <td className="py-2">이윤 ({(detailedCost.profit_rate * 100).toFixed(0)}%)</td>
                      <td className="text-right py-2">{formatCost(detailedCost.profit_cost)}</td>
                    </tr>
                    {detailedCost.extra_cost > 0 && (
                      <tr className="border-b border-slate-700/50">
                        <td className="py-2">추가 비용 {detailedCost.extra_detail && `(${detailedCost.extra_detail})`}</td>
                        <td className="text-right py-2">{formatCost(detailedCost.extra_cost)}</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
              
              {/* 최종 합계 */}
              <div className="bg-accent/20 rounded-lg p-4 flex justify-between items-center">
                <span className="text-lg font-medium text-slate-200">최종 공사비</span>
                <span className="text-xl font-bold text-accent">{formatCost(detailedCost.total)}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
