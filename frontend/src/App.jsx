import { useEffect, useState, useCallback, useRef } from 'react'
import MapView from './components/Map/MapView'
import ControlPanel from './components/Panel/ControlPanel'
import ResultPanel from './components/Panel/ResultPanel'
import CostDetailModal from './components/Panel/CostDetailModal'
import Toast from './components/common/Toast'
import LoginPage from './components/Auth/LoginPage'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { useDesign } from './hooks/useDesign'
import { getFacilitiesByBbox, getFacilities } from './services/api'

/**
 * ELBIX AIDD 메인 애플리케이션
 * AI 기반 배전 설계 자동화 시스템
 */
function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

/**
 * 앱 메인 컨텐츠
 * - 인증 상태에 따라 로그인 페이지 또는 메인 화면 표시
 */
function AppContent() {
  const { isAuthenticated, loading: authLoading, username, logout } = useAuth()
  // 수용가 좌표 상태
  const [consumerCoord, setConsumerCoord] = useState(null)
  
  // 상(Phase) 선택 상태 ("1": 단상, "3": 3상)
  const [phaseCode, setPhaseCode] = useState("1")
  
  // 선택된 경로 인덱스
  const [selectedRouteIndex, setSelectedRouteIndex] = useState(0)
  
  // 토스트 메시지
  const [toast, setToast] = useState(null)
  
  // 시설물 표시 여부
  const [showFacilities, setShowFacilities] = useState(false)
  
    // 시설물 데이터 및 요청 관리
    const [facilities, setFacilities] = useState(null)
    const abortControllerRef = useRef(null)
    
    // 시설물 로딩 중 여부
    const [facilitiesLoading, setFacilitiesLoading] = useState(false)
    
    // 비용 상세 모달 상태
    const [costModalRoute, setCostModalRoute] = useState(null)
    
    // 현재 뷰포트 bbox
    const [currentBbox, setCurrentBbox] = useState(null)
    
    // 저장된 경로 목록
    const [savedRoutes, setSavedRoutes] = useState([])
    
    // 지도 참조
    const mapRef = useRef(null)
    const autoRefreshTimerRef = useRef(null)
    
    // 설계 API 훅
    const {
      loading,
      result,
      error,
      runDesign,
      clearResult
    } = useDesign()
    
    // 지도 클릭 핸들러
    const handleMapClick = useCallback((coord) => {
      setConsumerCoord(coord)
      clearResult()
      setSelectedRouteIndex(0)
    }, [clearResult])
    
    // 좌표 선택 취소 핸들러
    const handleClearCoord = useCallback(() => {
      setConsumerCoord(null)
      clearResult()
      setSelectedRouteIndex(0)
    }, [clearResult])
    
    // 설계 실행 핸들러
    const handleRunDesign = useCallback(async () => {
      if (!consumerCoord) {
        setToast({ type: 'warning', message: '지도에서 수용가 위치를 선택하세요' })
        return
      }
      
      try {
        await runDesign(consumerCoord, phaseCode)
        setSelectedRouteIndex(0)
      } catch (err) {
        setToast({ type: 'error', message: err.message })
      }
    }, [consumerCoord, phaseCode, runDesign])
    
    // 좌표 직접 입력 핸들러
    const handleCoordChange = useCallback((coord) => {
      setConsumerCoord(coord)
      clearResult()
    }, [clearResult])
    
    // 경로 선택 핸들러
    const handleRouteSelect = useCallback((index) => {
      setSelectedRouteIndex(index)
    }, [])
    
    // 현재 위치로 이동
    const handleGoToCurrentLocation = useCallback(() => {
      if (!navigator.geolocation) {
        setToast({ type: 'warning', message: '이 브라우저에서 위치 정보를 지원하지 않습니다.' })
        return
      }
      
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { longitude, latitude } = position.coords
          // WGS84 → EPSG:3857 변환
          const x = longitude * 20037508.34 / 180
          let y = Math.log(Math.tan((90 + latitude) * Math.PI / 360)) / (Math.PI / 180)
          y = y * 20037508.34 / 180
          
          if (mapRef.current) {
            mapRef.current.panTo([x, y])
          }
          setToast({ type: 'success', message: '현재 위치로 이동했습니다.' })
        },
        (error) => {
          setToast({ type: 'error', message: '위치 정보를 가져올 수 없습니다.' })
        }
      )
    }, [])
    
    // [수정] 시설물 로드 핸들러 (수용가 좌표 기준 400m 반경)
    const handleLoadFacilities = useCallback(async (centerCoord = null, isAuto = false) => {
      // 명시적 좌표가 없으면 현재 설정된 수용가 좌표 사용
      const targetCoord = centerCoord || consumerCoord
      
      if (!targetCoord) {
        if (!isAuto) setToast({ type: 'warning', message: '수용가 위치를 먼저 선택해주세요.' })
        return
      }
  
      // 이전 요청 취소 및 새 컨트롤러 생성
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
      abortControllerRef.current = new AbortController()
      
      setFacilitiesLoading(true)
      if (!isAuto) setToast({ type: 'info', message: '시설물 로드 중...' })
      
      try {
        const coordStr = `${targetCoord[0]},${targetCoord[1]}`
        // bbox_size=400 (반경이 아니라 BBox 크기이므로 반경 200m 효과, 
        // 요구사항이 "반경 400m"라면 bbox_size=800이 되어야 함. 
        // 하지만 기존 BBOX_SIZE 상수가 400이므로 일단 400 사용하거나 800으로 설정)
        // 여기서는 안전하게 800 (반경 400m 커버) 사용
        const params = { coord: coordStr, bbox_size: 800 } 
        
        // getFacilities (coord 기반) API 사용 (api.js에 이미 import 되어 있어야 함)
        // import { getFacilitiesByBbox } -> import { getFacilities } 로 변경 필요
        // 하지만 App.jsx 상단 import를 보면 getFacilitiesByBbox만 되어있을 수 있음.
        // 따라서 api.js에서 getFacilities를 import 해야 함.
        // 이 코드 블록은 함수 내부이므로 외부 import 구문은 별도로 수정해야 함.
        // 일단 여기서는 기존 getFacilitiesByBbox 대신 getFacilities를 호출한다고 가정하고 작성.
        // 실제로는 상단 import 수정이 필요함.
        
        // 임시: api.js의 getFacilities 함수를 사용하기 위해 동적 import 또는 상단 수정 필요.
        // 여기서는 handleLoadFacilities를 교체하는 것이므로, 아래에서 import 문 수정도 같이 요청하겠음.
        
        // getFacilities는 params 객체를 받음
        // 여기서는 getFacilities 함수가 import 되어 있다고 가정
        const data = await getFacilities(params)
  
        // 요청이 취소되었으면 중단
        if (!data || abortControllerRef.current.signal.aborted) return
  
        setFacilities(data)
        
        if (!isAuto) {
          setShowFacilities(true)
          setToast({ type: 'success', message: '시설물 로드 완료' })
        }
      } catch (err) {
        if (err.name === 'CanceledError' || err.name === 'AbortError') return
        console.error('시설물 로드 오류:', err)
        if (!isAuto) setToast({ type: 'error', message: err.message || `시설물 조회 실패` })
      } finally {
        setFacilitiesLoading(false)
      }
    }, [consumerCoord])
    
    // 시설물 표시 토글 핸들러
    const handleToggleFacilities = useCallback(() => {
      if (showFacilities) {
        setShowFacilities(false)
        if (abortControllerRef.current) abortControllerRef.current.abort()
        setFacilities(null)
      } else {
        if (consumerCoord) {
            setShowFacilities(true)
            handleLoadFacilities(consumerCoord)
        } else {
            setToast({ type: 'warning', message: '수용가 위치를 먼저 선택해주세요.' })
        }
      }
    }, [showFacilities, consumerCoord, handleLoadFacilities])  
  
  // 지도 뷰 변경 핸들러 (더 이상 자동 로드에 사용되지 않음, 상태만 업데이트하거나 삭제)
  const handleViewChange = useCallback((bbox) => {
    setCurrentBbox(bbox)
  }, [])

  // [수정] 수용가 좌표 변경 시 시설물 자동 로드/해제
  useEffect(() => {
    if (consumerCoord) {
      setShowFacilities(true)
      handleLoadFacilities(consumerCoord, true)
    } else {
      setShowFacilities(false)
      setFacilities(null)
    }
  }, [consumerCoord, handleLoadFacilities])
  
  // 시설물 새로고침 핸들러
  const handleRefreshFacilities = useCallback(() => {
    if (showFacilities && consumerCoord) {
      handleLoadFacilities(consumerCoord)
    }
  }, [showFacilities, consumerCoord, handleLoadFacilities])
  
  // 경로 저장 핸들러
  const handleSaveRoute = useCallback((route) => {
    const savedItem = {
      id: Date.now(),
      savedAt: new Date().toISOString(),
      consumerCoord: consumerCoord,
      phaseCode: phaseCode,
      requestSpec: phaseCode === '3' ? '3상' : '단상',
      route: route
    }
    setSavedRoutes(prev => [...prev, savedItem])
    setToast({ type: 'success', message: '경로가 저장되었습니다.' })
  }, [consumerCoord, phaseCode])
  
  // 저장된 경로 삭제 핸들러
  const handleRemoveSavedRoute = useCallback((id) => {
    setSavedRoutes(prev => prev.filter(item => item.id !== id))
    setToast({ type: 'info', message: '저장된 경로가 삭제되었습니다.' })
  }, [])
  
  // 저장 목록 전체 삭제 핸들러
  const handleClearSavedRoutes = useCallback(() => {
    setSavedRoutes([])
    setToast({ type: 'info', message: '저장 목록이 비워졌습니다.' })
  }, [])
  
  // 인증 확인 중 로딩 화면
  if (authLoading) {
    return (
      <div className="h-full w-full flex items-center justify-center bg-bg-primary">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-accent border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-400">인증 확인 중...</p>
        </div>
      </div>
    )
  }
  
  // 비로그인 시 로그인 페이지 표시
  if (!isAuthenticated) {
    return <LoginPage />
  }
  
  return (
    <div className="h-full w-full flex flex-col bg-bg-primary">
      {/* 헤더 */}
      <header className="h-14 bg-bg-secondary border-b border-slate-700 flex items-center px-6 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-accent rounded-lg flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div>
            <h1 className="text-lg font-semibold text-white tracking-tight">ELBIX AIDD</h1>
            <p className="text-xs text-slate-400 -mt-0.5">AI 기반 배전 설계 자동화</p>
          </div>
        </div>
        
        {/* 상태 표시 */}
        <div className="ml-auto flex items-center gap-4">
          {loading && (
            <div className="flex items-center gap-2 text-accent">
              <div className="w-4 h-4 border-2 border-accent border-t-transparent rounded-full animate-spin" />
              <span className="text-sm">설계 분석 중...</span>
            </div>
          )}
          {facilitiesLoading && (
            <div className="flex items-center gap-2 text-amber-400">
              <div className="w-4 h-4 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
              <span className="text-sm">시설물 로드 중...</span>
            </div>
          )}
          {result && result.status === 'success' && (
            <div className="flex items-center gap-2 text-green-400">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-sm">{result.routes?.length || 0}개 경로 발견</span>
            </div>
          )}
          
          {/* 사용자 정보 및 로그아웃 */}
          <div className="flex items-center gap-3 ml-4 pl-4 border-l border-slate-600">
            <div className="flex items-center gap-2 text-slate-300">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              <span className="text-sm">{username}</span>
            </div>
            <button
              onClick={logout}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-slate-400 
                       hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              로그아웃
            </button>
          </div>
        </div>
      </header>
      
      {/* 메인 컨텐츠 */}
      <main className="flex-1 flex overflow-hidden">
        {/* 좌측 패널 - 제어 패널 */}
        <aside className="w-72 bg-bg-secondary border-r border-slate-700 flex flex-col shrink-0">
          <ControlPanel
            coord={consumerCoord}
            phaseCode={phaseCode}
            loading={loading}
            showFacilities={showFacilities}
            facilitiesLoading={facilitiesLoading}
            savedRoutes={savedRoutes}
            onCoordChange={handleCoordChange}
            onPhaseChange={setPhaseCode}
            onRunDesign={handleRunDesign}
            onClearCoord={handleClearCoord}
            onLoadFacilities={handleLoadFacilities}
            onToggleFacilities={handleToggleFacilities}
            onRefreshFacilities={handleRefreshFacilities}
            onRemoveSavedRoute={handleRemoveSavedRoute}
            onClearSavedRoutes={handleClearSavedRoutes}
          />
        </aside>
        
        {/* 지도 영역 */}
        <div className="flex-1 relative">
          <MapView
            ref={mapRef}
            consumerCoord={consumerCoord}
            result={result}
            facilities={facilities}
            showFacilities={showFacilities}
            selectedRouteIndex={selectedRouteIndex}
            onMapClick={handleMapClick}
            onGoToCurrentLocation={handleGoToCurrentLocation}
            onViewChange={handleViewChange}
          />
        </div>
        
        {/* 우측 패널 - 결과 패널 (결과가 있을 때만 표시) */}
        {(result || error) && (
          <aside className="w-96 bg-bg-secondary border-l border-slate-700 flex flex-col shrink-0">
            <ResultPanel
              result={result}
              error={error}
              selectedIndex={selectedRouteIndex}
              onSelectRoute={handleRouteSelect}
              onShowCostDetail={(route) => setCostModalRoute(route)}
              onSaveRoute={handleSaveRoute}
              requestSpec={phaseCode === '3' ? '3상' : '단상'}
            />
          </aside>
        )}
      </main>
      
      {/* 토스트 */}
      {toast && (
        <Toast
          type={toast.type}
          message={toast.message}
          onClose={() => setToast(null)}
        />
      )}
      
      {/* 비용 상세 모달 */}
      <CostDetailModal
        route={costModalRoute}
        isOpen={!!costModalRoute}
        onClose={() => setCostModalRoute(null)}
      />
    </div>
  )
}

export default App
