import { useState, useCallback } from 'react'
import { runDesignApi } from '../services/api'

/**
 * 설계 API 커스텀 훅
 * @returns {Object} 설계 상태 및 함수
 */
export function useDesign() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  
  /**
   * 설계 실행
   * @param {number[]} coord - [x, y] 좌표 (EPSG:3857)
   * @param {string} phaseCode - 상 코드 ("1" 또는 "3")
   * @returns {Promise<Object>} 설계 결과
   */
  const runDesign = useCallback(async (coord, phaseCode) => {
    setLoading(true)
    setError(null)
    
    try {
      const coordStr = `${coord[0]},${coord[1]}`
      
      const response = await runDesignApi({
        coord: coordStr,
        phase_code: phaseCode,
      })
      
      setResult(response)
      return response
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])
  
  /**
   * 결과 초기화
   */
  const clearResult = useCallback(() => {
    setResult(null)
    setError(null)
  }, [])
  
  return {
    loading,
    result,
    error,
    runDesign,
    clearResult,
  }
}

export default useDesign
