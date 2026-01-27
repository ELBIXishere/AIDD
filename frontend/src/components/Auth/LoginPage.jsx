import { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'

/**
 * 로그인 페이지 컴포넌트
 * - ID/PW 입력 폼
 * - 로그인 버튼
 * - 에러 메시지 표시
 */
export default function LoginPage() {
  // 폼 입력 상태
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  
  // 로그인 중 상태
  const [isLoggingIn, setIsLoggingIn] = useState(false)
  
  // 인증 컨텍스트
  const { login, error, clearError } = useAuth()
  
  /**
   * 로그인 폼 제출 핸들러
   */
  const handleSubmit = async (e) => {
    e.preventDefault()
    
    // 입력값 검증
    if (!username.trim() || !password.trim()) {
      return
    }
    
    setIsLoggingIn(true)
    clearError()
    
    try {
      await login(username.trim(), password)
    } finally {
      setIsLoggingIn(false)
    }
  }
  
  /**
   * 입력 필드 변경 핸들러
   */
  const handleInputChange = (setter) => (e) => {
    setter(e.target.value)
    if (error) {
      clearError()
    }
  }
  
  return (
    <div className="min-h-screen bg-bg-primary flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* 로고 및 타이틀 */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-accent rounded-2xl flex items-center justify-center mx-auto mb-4">
            <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">ELBIX AIDD</h1>
          <p className="text-slate-400">AI 기반 배전 설계 자동화 시스템</p>
        </div>
        
        {/* 로그인 카드 */}
        <div className="bg-bg-secondary rounded-2xl border border-slate-700 p-8">
          <h2 className="text-lg font-semibold text-white mb-6 text-center">관리자 로그인</h2>
          
          {/* 에러 메시지 */}
          {error && (
            <div className="mb-6 p-4 bg-red-900/30 border border-red-700 rounded-lg">
              <div className="flex items-center gap-2 text-red-400">
                <svg className="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                    d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="text-sm">{error}</span>
              </div>
            </div>
          )}
          
          {/* 로그인 폼 */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* 아이디 입력 */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-slate-300 mb-2">
                아이디
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={handleInputChange(setUsername)}
                placeholder="아이디를 입력하세요"
                className="w-full px-4 py-3 bg-bg-primary border border-slate-600 rounded-lg 
                         text-white placeholder-slate-500
                         focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent
                         transition-colors"
                autoComplete="username"
                autoFocus
                disabled={isLoggingIn}
              />
            </div>
            
            {/* 비밀번호 입력 */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-300 mb-2">
                비밀번호
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={handleInputChange(setPassword)}
                placeholder="비밀번호를 입력하세요"
                className="w-full px-4 py-3 bg-bg-primary border border-slate-600 rounded-lg 
                         text-white placeholder-slate-500
                         focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent
                         transition-colors"
                autoComplete="current-password"
                disabled={isLoggingIn}
              />
            </div>
            
            {/* 로그인 버튼 */}
            <button
              type="submit"
              disabled={isLoggingIn || !username.trim() || !password.trim()}
              className="w-full py-3 px-4 bg-accent hover:bg-accent/90 
                       disabled:bg-slate-600 disabled:cursor-not-allowed
                       text-white font-medium rounded-lg
                       transition-colors flex items-center justify-center gap-2"
            >
              {isLoggingIn ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>로그인 중...</span>
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                      d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                  </svg>
                  <span>로그인</span>
                </>
              )}
            </button>
          </form>
        </div>
        
        {/* 푸터 */}
        <p className="text-center text-slate-500 text-sm mt-6">
          &copy; 2026 ELBIX. All rights reserved.
        </p>
      </div>
    </div>
  )
}
