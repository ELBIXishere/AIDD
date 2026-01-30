import axios from 'axios'

/**
 * ELBIX AIDD API 클라이언트
 */

// API 기본 URL
// 개발 모드에서는 절대 URL(예: http://192.168.0.64:8000/api/v1) 사용 시 크로스 오리진으로 쿠키가 안 붙을 수 있음.
// 개발 시에는 VITE_API_URL 비우거나 '/api/v1'로 두어 프록시를 타게 하는 것을 권장.
const rawApiBase = import.meta.env.VITE_API_URL || '/api/v1'
const API_BASE_URL = (import.meta.env.DEV && (rawApiBase || '').startsWith('http'))
  ? '/api/v1'
  : (rawApiBase || '/api/v1')

// Axios 인스턴스 생성
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60초 (설계 분석에 시간 소요)
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // 쿠키 전송을 위해 필수 (세션 인증)
})

// 요청 인터셉터
api.interceptors.request.use(
  (config) => {
    // 개발 전용: 쿠키/프록시 이슈 시 세션 대신 헤더로 인증 (백엔드 DEBUG 시에만 유효, 배포 빌드엔 미포함)
    if (import.meta.env.DEV) {
      config.headers['X-Dev-Auth'] = 'admin'
    }
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`, config.data)
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 응답 인터셉터: 401 시 세션 만료 처리
api.interceptors.response.use(
  (response) => {
    console.log(`[API] Response:`, response.data)
    return response
  },
  (error) => {
    console.error('[API] Error:', error.response?.data || error.message)
    // 401 시: 시설물 조회는 로그아웃하지 않고 토스트만 표시 (쿠키/프록시 이슈 시에도 화면 유지)
    const isFacilities = /\/facilities(\?|$)/.test(error.config?.url ?? '')
    if (error.response?.status === 401 && !isFacilities) {
      window.dispatchEvent(new CustomEvent('auth:session-expired'))
      const unified = '세션이 만료되었습니다. 다시 로그인해 주세요.'
      error.message = unified
      if (error.response?.data && typeof error.response.data === 'object') {
        error.response.data.detail = unified
      }
    }
    return Promise.reject(error)
  }
)

/**
 * 설계 API 호출
 * @param {Object} params - 설계 요청 파라미터
 * @param {string} params.coord - 좌표 문자열 "x,y" (EPSG:3857)
 * @param {string} params.phase_code - 상 코드 ("1" 또는 "3")
 * @param {string} [params.gis_wfs_url] - GIS WFS URL (선택)
 * @param {string} [params.base_wfs_url] - BASE WFS URL (선택)
 * @param {string} [params.eps_url] - EPS URL (선택)
 * @returns {Promise<Object>} 설계 결과
 */
export async function runDesignApi(params) {
  try {
    const response = await api.post('/design', params)
    return response.data
  } catch (error) {
    if (error.response) {
      // 서버 에러 응답
      const message = error.response.data?.detail || '설계 처리 중 오류가 발생했습니다.'
      throw new Error(message)
    } else if (error.request) {
      // 네트워크 에러
      throw new Error('서버에 연결할 수 없습니다. 네트워크를 확인하세요.')
    } else {
      throw new Error(error.message)
    }
  }
}

/**
 * 서버 헬스 체크
 * @returns {Promise<boolean>}
 */
export async function checkHealth() {
  try {
    const response = await api.get('/health')
    return response.data?.status === 'ok'
  } catch {
    return false
  }
}

/**
 * 시설물 조회 API (bbox 기반) - 세션 쿠키 자동 전송
 * @param {string} bboxString - 영역 문자열 "minX,minY,maxX,maxY" (EPSG:3857)
 * @param {number} [maxFeatures=5000] - 레이어별 최대 피처 수
 * @param {AbortSignal} [signal] - 요청 취소용 시그널
 * @returns {Promise<Object>} 시설물 데이터
 */
export async function getFacilitiesByBbox(bboxString, maxFeatures = 5000, signal = null) {
  try {
    const response = await api.get('/facilities', {
      params: { bbox: bboxString, max_features: maxFeatures },
      signal: signal
    })
    return response.data
  } catch (error) {
    if (axios.isCancel(error)) {
      // 취소된 요청은 에러를 던지지 않음 (조용히 종료)
      return null
    }
    if (error.response) {
      const message = error.response.data?.detail || '시설물 조회 중 오류가 발생했습니다.'
      throw new Error(message)
    } else if (error.request) {
      throw new Error('서버에 연결할 수 없습니다. 네트워크를 확인하세요.')
    } else {
      throw new Error(error.message)
    }
  }
}

/**
 * 시설물 조회 API (coord 기반, 레거시)
 * @param {Object} params - 조회 파라미터
 * @param {string} params.coord - 중심 좌표 "x,y" (EPSG:3857)
 * @param {number} [params.bbox_size=400] - 조회 영역 크기 (미터)
 * @returns {Promise<Object>} 시설물 데이터 (전주, 전선)
 */
export async function getFacilities(params) {
  try {
    const { coord, bbox_size = 400 } = params
    const response = await api.get('/facilities', {
      params: { coord, bbox_size }
    })
    return response.data
  } catch (error) {
    if (error.response) {
      const message = error.response.data?.detail || '시설물 조회 중 오류가 발생했습니다.'
      throw new Error(message)
    } else if (error.request) {
      throw new Error('서버에 연결할 수 없습니다. 네트워크를 확인하세요.')
    } else {
      throw new Error(error.message)
    }
  }
}

/**
 * 설계 서비스 상태 조회
 * @returns {Promise<Object>} 서비스 상태 정보
 */
export async function getDesignStatus() {
  try {
    const response = await api.get('/design/status')
    return response.data
  } catch (error) {
    console.error('설계 서비스 상태 조회 실패:', error)
    return null
  }
}

// ===== 인증 API =====

/**
 * 로그인 API
 * @param {string} username - 사용자 ID
 * @param {string} password - 비밀번호
 * @returns {Promise<Object>} 로그인 결과
 */
export async function loginApi(username, password) {
  try {
    const response = await api.post('/auth/login', { username, password })
    return response.data
  } catch (error) {
    if (error.response) {
      const message = error.response.data?.detail || '로그인에 실패했습니다.'
      throw new Error(message)
    } else if (error.request) {
      throw new Error('서버에 연결할 수 없습니다.')
    } else {
      throw new Error(error.message)
    }
  }
}

/**
 * 로그아웃 API
 * @returns {Promise<Object>} 로그아웃 결과
 */
export async function logoutApi() {
  try {
    const response = await api.post('/auth/logout')
    return response.data
  } catch (error) {
    console.error('로그아웃 오류:', error)
    throw error
  }
}

/**
 * 현재 인증 상태 확인 API
 * @returns {Promise<Object>} 인증 상태 { authenticated: boolean, username: string }
 */
export async function checkAuthApi() {
  try {
    const response = await api.get('/auth/me')
    return response.data
  } catch (error) {
    // 인증 확인 실패 시 미인증 상태로 처리
    return { authenticated: false, username: null }
  }
}

export default api
