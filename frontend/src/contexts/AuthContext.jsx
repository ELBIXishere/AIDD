import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { loginApi, logoutApi, checkAuthApi } from '../services/api'

/**
 * 인증 컨텍스트
 * - 전역 인증 상태 관리
 * - 로그인/로그아웃 함수 제공
 */

// 인증 컨텍스트 생성
const AuthContext = createContext(null)

/**
 * 인증 컨텍스트 Provider
 */
export function AuthProvider({ children }) {
  // 인증 상태
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  
  // 현재 로그인된 사용자 이름
  const [username, setUsername] = useState(null)
  
  // 로딩 상태 (초기 인증 확인 중)
  const [loading, setLoading] = useState(true)
  
  // 로그인 에러 메시지
  const [error, setError] = useState(null)
  
  /**
   * 초기 인증 상태 확인
   * - 페이지 로드 시 세션 쿠키로 인증 상태 확인
   */
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const response = await checkAuthApi()
        if (response.authenticated) {
          setIsAuthenticated(true)
          setUsername(response.username)
        } else {
          setIsAuthenticated(false)
          setUsername(null)
        }
      } catch (err) {
        console.error('인증 상태 확인 오류:', err)
        setIsAuthenticated(false)
        setUsername(null)
      } finally {
        setLoading(false)
      }
    }
    
    checkAuth()
  }, [])

  /**
   * 401(세션 만료) 시 로그아웃 처리
   * - API 응답 인터셉터에서 auth:session-expired 이벤트 발생
   */
  useEffect(() => {
    const onSessionExpired = () => {
      setIsAuthenticated(false)
      setUsername(null)
      setError(null)
    }
    window.addEventListener('auth:session-expired', onSessionExpired)
    return () => window.removeEventListener('auth:session-expired', onSessionExpired)
  }, [])
  
  /**
   * 로그인 함수
   * @param {string} inputUsername - 사용자 ID
   * @param {string} password - 비밀번호
   * @returns {Promise<boolean>} 로그인 성공 여부
   */
  const login = useCallback(async (inputUsername, password) => {
    setError(null)
    
    try {
      const response = await loginApi(inputUsername, password)
      
      if (response.success) {
        setIsAuthenticated(true)
        setUsername(response.username)
        return true
      } else {
        setError(response.message || '로그인에 실패했습니다.')
        return false
      }
    } catch (err) {
      setError(err.message || '로그인 중 오류가 발생했습니다.')
      return false
    }
  }, [])
  
  /**
   * 로그아웃 함수
   */
  const logout = useCallback(async () => {
    try {
      await logoutApi()
    } catch (err) {
      console.error('로그아웃 오류:', err)
    } finally {
      // API 호출 성공/실패와 관계없이 로컬 상태 초기화
      setIsAuthenticated(false)
      setUsername(null)
      setError(null)
    }
  }, [])
  
  /**
   * 에러 초기화 함수
   */
  const clearError = useCallback(() => {
    setError(null)
  }, [])
  
  // 컨텍스트 값
  const value = {
    isAuthenticated,
    username,
    loading,
    error,
    login,
    logout,
    clearError
  }
  
  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

/**
 * 인증 컨텍스트 사용 훅
 * @returns {Object} 인증 컨텍스트 값
 */
export function useAuth() {
  const context = useContext(AuthContext)
  
  if (!context) {
    throw new Error('useAuth는 AuthProvider 내에서 사용해야 합니다.')
  }
  
  return context
}

export default AuthContext
