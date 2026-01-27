/**
 * 좌표 변환 유틸리티
 */

/**
 * EPSG:4326 (WGS84) → EPSG:3857 (Web Mercator) 변환
 * @param {number} lon - 경도
 * @param {number} lat - 위도
 * @returns {number[]} [x, y]
 */
export function toEPSG3857(lon, lat) {
  const x = lon * 20037508.34 / 180
  let y = Math.log(Math.tan((90 + lat) * Math.PI / 360)) / (Math.PI / 180)
  y = y * 20037508.34 / 180
  return [x, y]
}

/**
 * EPSG:3857 → EPSG:4326 변환
 * @param {number} x - X 좌표
 * @param {number} y - Y 좌표
 * @returns {number[]} [lon, lat]
 */
export function toEPSG4326(x, y) {
  const lon = x * 180 / 20037508.34
  let lat = y * 180 / 20037508.34
  lat = Math.atan(Math.exp(lat * Math.PI / 180)) * 360 / Math.PI - 90
  return [lon, lat]
}

/**
 * 두 점 사이 거리 계산 (EPSG:3857)
 * @param {number[]} coord1 - [x1, y1]
 * @param {number[]} coord2 - [x2, y2]
 * @returns {number} 거리 (미터)
 */
export function calculateDistance(coord1, coord2) {
  const dx = coord2[0] - coord1[0]
  const dy = coord2[1] - coord1[1]
  return Math.sqrt(dx * dx + dy * dy)
}

/**
 * 좌표 문자열 파싱
 * @param {string} coordStr - "x,y" 형식
 * @returns {number[]|null} [x, y] 또는 null
 */
export function parseCoordString(coordStr) {
  if (!coordStr) return null
  
  const parts = coordStr.split(',').map(s => parseFloat(s.trim()))
  if (parts.length !== 2 || parts.some(isNaN)) return null
  
  return parts
}

/**
 * 좌표를 문자열로 변환
 * @param {number[]} coord - [x, y]
 * @param {number} precision - 소수점 자릿수
 * @returns {string} "x,y"
 */
export function formatCoordString(coord, precision = 2) {
  if (!coord || coord.length !== 2) return ''
  return `${coord[0].toFixed(precision)},${coord[1].toFixed(precision)}`
}

/**
 * 좌표 유효성 검사 (한국 범위)
 * @param {number[]} coord - [x, y] (EPSG:3857)
 * @returns {boolean}
 */
export function isValidKoreaCoord(coord) {
  if (!coord || coord.length !== 2) return false
  
  // 한국 범위 (EPSG:3857)
  const minX = 13800000 // 약 124°E
  const maxX = 14600000 // 약 131°E
  const minY = 3800000  // 약 33°N
  const maxY = 4700000  // 약 39°N
  
  return coord[0] >= minX && coord[0] <= maxX &&
         coord[1] >= minY && coord[1] <= maxY
}
