import { useRef, useCallback } from 'react'
import { fromLonLat, toLonLat } from 'ol/proj'

/**
 * 지도 관련 유틸리티 훅
 */
export function useMap() {
  const mapRef = useRef(null)
  
  /**
   * 지도 인스턴스 설정
   * @param {Map} map - OpenLayers Map 인스턴스
   */
  const setMap = useCallback((map) => {
    mapRef.current = map
  }, [])
  
  /**
   * 특정 좌표로 이동
   * @param {number[]} coord - [x, y] 좌표 (EPSG:3857)
   * @param {number} zoom - 줌 레벨
   */
  const panTo = useCallback((coord, zoom = 16) => {
    if (!mapRef.current) return
    
    mapRef.current.getView().animate({
      center: coord,
      zoom,
      duration: 500,
    })
  }, [])
  
  /**
   * 경도/위도를 EPSG:3857로 변환
   * @param {number} lon - 경도
   * @param {number} lat - 위도
   * @returns {number[]} [x, y]
   */
  const toMapCoord = useCallback((lon, lat) => {
    return fromLonLat([lon, lat])
  }, [])
  
  /**
   * EPSG:3857을 경도/위도로 변환
   * @param {number[]} coord - [x, y]
   * @returns {number[]} [lon, lat]
   */
  const toLonLatCoord = useCallback((coord) => {
    return toLonLat(coord)
  }, [])
  
  return {
    map: mapRef.current,
    setMap,
    panTo,
    toMapCoord,
    toLonLatCoord,
  }
}

export default useMap
