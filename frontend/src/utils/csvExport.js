/**
 * CSV 내보내기 유틸리티
 * - 설계 결과를 CSV 형식으로 변환 및 다운로드
 */

/**
 * 현재 날짜/시간을 YYYYMMDD_HHMMSS 형식으로 반환
 * @returns {string} 포맷된 날짜/시간 문자열
 */
function getFormattedDateTime() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  const seconds = String(now.getSeconds()).padStart(2, '0')
  
  return `${year}${month}${day}_${hours}${minutes}${seconds}`
}

/**
 * 값을 CSV 셀에 안전하게 변환 (쉼표, 따옴표 처리)
 * @param {any} value - 변환할 값
 * @returns {string} CSV 안전 문자열
 */
function escapeCSVValue(value) {
  if (value === null || value === undefined) {
    return ''
  }
  
  const stringValue = String(value)
  
  // 쉼표, 따옴표, 줄바꿈이 포함된 경우 따옴표로 감싸기
  if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
    // 따옴표는 두 개로 이스케이프
    return `"${stringValue.replace(/"/g, '""')}"`
  }
  
  return stringValue
}

/**
 * 좌표 배열을 JSON 문자열로 변환
 * @param {Array} coords - 좌표 배열 [[x, y], ...]
 * @returns {string} JSON 문자열
 */
function coordsToJson(coords) {
  if (!coords || !Array.isArray(coords) || coords.length === 0) {
    return ''
  }
  return JSON.stringify(coords)
}

/**
 * 설계 결과를 CSV 문자열로 변환
 * @param {Object} result - 설계 결과 객체
 * @returns {string} CSV 문자열
 */
function resultToCSV(result) {
  if (!result || !result.routes || result.routes.length === 0) {
    return ''
  }
  
  // CSV 헤더 (전체 정보 포함)
  const headers = [
    '순위',
    '시작전주ID',
    '시작전주좌표X',
    '시작전주좌표Y',
    '총거리(m)',
    '총비용(원)',
    '비용지수',
    '신설전주수',
    '전주비용(원)',
    '전선비용(원)',
    '인건비(원)',
    '전압강하(%)',
    '전압강하허용',
    '전주규격',
    '전선규격',
    '기설전주전압',
    '기설전주상',
    '신설전주좌표',
    '경로좌표'
  ]
  
  // CSV 행 생성
  const rows = result.routes.map(route => {
    // 시작 전주 좌표
    const startCoordX = route.start_pole_coord?.[0] || ''
    const startCoordY = route.start_pole_coord?.[1] || ''
    
    // 전압 강하 정보
    const voltageDrop = route.voltage_drop?.voltage_drop_percent?.toFixed(2) || ''
    const voltageDropAcceptable = route.voltage_drop?.is_acceptable ? 'Y' : 'N'
    
    // 전압/상 정보
    const sourceVoltage = route.source_voltage_type === 'HV' ? '고압' : 
                         route.source_voltage_type === 'LV' ? '저압' : ''
    const sourcePhase = route.source_phase_type === '3' ? '3상' : 
                       route.source_phase_type === '1' ? '단상' : ''
    
    return [
      route.rank || '',
      route.start_pole_id || '',
      startCoordX,
      startCoordY,
      route.total_distance?.toFixed(1) || '',
      route.total_cost || '',
      route.cost_index || '',
      route.new_poles_count || 0,
      route.pole_cost || 0,
      route.wire_cost || 0,
      route.labor_cost || 0,
      voltageDrop,
      voltageDropAcceptable,
      route.pole_spec || '',
      route.wire_spec || '',
      sourceVoltage,
      sourcePhase,
      coordsToJson(route.new_pole_coordinates),
      coordsToJson(route.path_coordinates)
    ].map(escapeCSVValue)
  })
  
  // BOM + 헤더 + 데이터 행 결합
  // BOM: Excel에서 한글 인코딩을 위해 필요
  const BOM = '\uFEFF'
  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.join(','))
  ].join('\n')
  
  return BOM + csvContent
}

/**
 * CSV 파일 다운로드
 * @param {Object} result - 설계 결과 객체
 * @param {string} [filename] - 파일명 (기본: 설계결과_YYYYMMDD_HHMMSS.csv)
 */
export function downloadCSV(result, filename) {
  const csvContent = resultToCSV(result)
  
  if (!csvContent) {
    console.error('CSV 생성 실패: 설계 결과가 없습니다.')
    return false
  }
  
  // 파일명 생성
  const defaultFilename = `설계결과_${getFormattedDateTime()}.csv`
  const finalFilename = filename || defaultFilename
  
  // Blob 생성 및 다운로드
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  
  const link = document.createElement('a')
  link.href = url
  link.download = finalFilename
  link.style.display = 'none'
  
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  // URL 해제
  URL.revokeObjectURL(url)
  
  return true
}

/**
 * 설계 결과 요약 정보를 포함한 CSV 다운로드
 * @param {Object} result - 설계 결과 객체
 */
export function downloadFullCSV(result) {
  if (!result) {
    console.error('설계 결과가 없습니다.')
    return false
  }
  
  // 메타데이터 섹션
  const metaHeaders = ['항목', '값']
  const metaRows = [
    ['요청규격', result.request_spec || ''],
    ['수용가좌표X', result.consumer_coord?.[0] || ''],
    ['수용가좌표Y', result.consumer_coord?.[1] || ''],
    ['처리상태', result.status || ''],
    ['처리시간(ms)', result.processing_time_ms || ''],
    ['요청부하(kW)', result.requested_load_kw || ''],
    ['경로수', result.routes?.length || 0],
    ['', ''], // 빈 줄
    ['=== 경로 상세 ===', '']
  ]
  
  // 경로 데이터 헤더
  const routeHeaders = [
    '순위',
    '시작전주ID',
    '시작전주좌표X',
    '시작전주좌표Y',
    '총거리(m)',
    '총비용(원)',
    '비용지수',
    '신설전주수',
    '전주비용(원)',
    '전선비용(원)',
    '인건비(원)',
    '전압강하(%)',
    '전압강하허용',
    '전주규격',
    '전선규격',
    '기설전주전압',
    '기설전주상',
    '신설전주좌표',
    '경로좌표'
  ]
  
  // 경로 데이터 행
  const routeRows = (result.routes || []).map(route => {
    const startCoordX = route.start_pole_coord?.[0] || ''
    const startCoordY = route.start_pole_coord?.[1] || ''
    const voltageDrop = route.voltage_drop?.voltage_drop_percent?.toFixed(2) || ''
    const voltageDropAcceptable = route.voltage_drop?.is_acceptable ? 'Y' : 'N'
    const sourceVoltage = route.source_voltage_type === 'HV' ? '고압' : 
                         route.source_voltage_type === 'LV' ? '저압' : ''
    const sourcePhase = route.source_phase_type === '3' ? '3상' : 
                       route.source_phase_type === '1' ? '단상' : ''
    
    return [
      route.rank || '',
      route.start_pole_id || '',
      startCoordX,
      startCoordY,
      route.total_distance?.toFixed(1) || '',
      route.total_cost || '',
      route.cost_index || '',
      route.new_poles_count || 0,
      route.pole_cost || 0,
      route.wire_cost || 0,
      route.labor_cost || 0,
      voltageDrop,
      voltageDropAcceptable,
      route.pole_spec || '',
      route.wire_spec || '',
      sourceVoltage,
      sourcePhase,
      coordsToJson(route.new_pole_coordinates),
      coordsToJson(route.path_coordinates)
    ].map(escapeCSVValue)
  })
  
  // CSV 조합
  const BOM = '\uFEFF'
  const csvLines = [
    // 메타데이터
    metaHeaders.join(','),
    ...metaRows.map(row => row.map(escapeCSVValue).join(',')),
    '', // 빈 줄
    // 경로 데이터
    routeHeaders.join(','),
    ...routeRows.map(row => row.join(','))
  ]
  
  const csvContent = BOM + csvLines.join('\n')
  
  // 다운로드
  const filename = `설계결과_${getFormattedDateTime()}.csv`
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.style.display = 'none'
  
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  URL.revokeObjectURL(url)
  
  return true
}

/**
 * 저장된 경로 목록을 CSV로 다운로드
 * @param {Array} savedRoutes - 저장된 경로 목록 배열
 * @returns {boolean} 성공 여부
 */
export function downloadSavedRoutesCSV(savedRoutes) {
  if (!savedRoutes || savedRoutes.length === 0) {
    console.error('저장된 경로가 없습니다.')
    return false
  }
  
  // CSV 헤더
  const headers = [
    '번호',
    '저장시간',
    '수용가좌표X',
    '수용가좌표Y',
    '요청규격',
    '시작전주ID',
    '시작전주좌표X',
    '시작전주좌표Y',
    '총거리(m)',
    '총비용(원)',
    '비용지수',
    '신설전주수',
    '전주비용(원)',
    '전선비용(원)',
    '인건비(원)',
    '전압강하(%)',
    '전압강하허용',
    '전주규격',
    '전선규격',
    '기설전주전압',
    '기설전주상',
    '신설전주좌표',
    '경로좌표'
  ]
  
  // CSV 행 생성
  const rows = savedRoutes.map((item, index) => {
    const route = item.route
    
    // 저장 시간 포맷
    const savedDate = new Date(item.savedAt)
    const formattedDate = `${savedDate.getFullYear()}-${String(savedDate.getMonth() + 1).padStart(2, '0')}-${String(savedDate.getDate()).padStart(2, '0')} ${String(savedDate.getHours()).padStart(2, '0')}:${String(savedDate.getMinutes()).padStart(2, '0')}:${String(savedDate.getSeconds()).padStart(2, '0')}`
    
    // 수용가 좌표
    const consumerX = item.consumerCoord?.[0] || ''
    const consumerY = item.consumerCoord?.[1] || ''
    
    // 시작 전주 좌표
    const startCoordX = route.start_pole_coord?.[0] || ''
    const startCoordY = route.start_pole_coord?.[1] || ''
    
    // 전압 강하 정보
    const voltageDrop = route.voltage_drop?.voltage_drop_percent?.toFixed(2) || ''
    const voltageDropAcceptable = route.voltage_drop?.is_acceptable ? 'Y' : 'N'
    
    // 전압/상 정보
    const sourceVoltage = route.source_voltage_type === 'HV' ? '고압' : 
                         route.source_voltage_type === 'LV' ? '저압' : ''
    const sourcePhase = route.source_phase_type === '3' ? '3상' : 
                       route.source_phase_type === '1' ? '단상' : ''
    
    return [
      index + 1,
      formattedDate,
      consumerX,
      consumerY,
      item.requestSpec || '',
      route.start_pole_id || '',
      startCoordX,
      startCoordY,
      route.total_distance?.toFixed(1) || '',
      route.total_cost || '',
      route.cost_index || '',
      route.new_poles_count || 0,
      route.pole_cost || 0,
      route.wire_cost || 0,
      route.labor_cost || 0,
      voltageDrop,
      voltageDropAcceptable,
      route.pole_spec || '',
      route.wire_spec || '',
      sourceVoltage,
      sourcePhase,
      coordsToJson(route.new_pole_coordinates),
      coordsToJson(route.path_coordinates)
    ].map(escapeCSVValue)
  })
  
  // BOM + 헤더 + 데이터 행 결합
  const BOM = '\uFEFF'
  const csvContent = BOM + [
    headers.join(','),
    ...rows.map(row => row.join(','))
  ].join('\n')
  
  // 다운로드
  const filename = `저장경로목록_${getFormattedDateTime()}.csv`
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.style.display = 'none'
  
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  URL.revokeObjectURL(url)
  
  return true
}

export default downloadCSV
