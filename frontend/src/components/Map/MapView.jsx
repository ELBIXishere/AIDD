import { useEffect, useRef, useState, forwardRef, useImperativeHandle, useCallback } from 'react'
import Map from 'ol/Map'
import View from 'ol/View'
import TileLayer from 'ol/layer/Tile'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import OSM from 'ol/source/OSM'
import XYZ from 'ol/source/XYZ'
import { fromLonLat, toLonLat } from 'ol/proj'
import Feature from 'ol/Feature'
import Point from 'ol/geom/Point'
import LineString from 'ol/geom/LineString'
import Polygon from 'ol/geom/Polygon'
import { Style, Fill, Stroke, Circle as CircleStyle, RegularShape, Text } from 'ol/style'
import { defaults as defaultControls, ScaleLine, ZoomSlider } from 'ol/control'

/**
 * OpenLayers 지도 컴포넌트
 * - 배경지도 (VWorld/OSM)
 * - 수용가 위치 표시
 * - 설계 결과 경로/전주 표시
 * - 시설물 표시 (전주, 전선, 변압기, 도로, 건물, 철도, 하천)
 */
const MapView = forwardRef(function MapView({ 
  consumerCoord, 
  result, 
  facilities,
  showFacilities = false,
  selectedRouteIndex = 0,
  onMapClick,
  onGoToCurrentLocation,
  onViewChange,  // bbox 변경 시 콜백
}, ref) {
  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)
  
  // 레이어 참조
  const consumerLayerRef = useRef(null)
  const routeLayerRef = useRef(null)
  const poleLayerRef = useRef(null)
  const facilityLayerRef = useRef(null)
  
  // 마우스 좌표 (실시간)
  const [mouseCoord, setMouseCoord] = useState(null)
  
  // 현재 뷰포트 bbox 계산 함수
  const getCurrentBbox = useCallback(() => {
    if (!mapInstanceRef.current) return null
    const view = mapInstanceRef.current.getView()
    const extent = view.calculateExtent(mapInstanceRef.current.getSize())
    // extent: [minX, minY, maxX, maxY]
    return {
      minX: extent[0],
      minY: extent[1],
      maxX: extent[2],
      maxY: extent[3],
      toString: () => `${extent[0]},${extent[1]},${extent[2]},${extent[3]}`
    }
  }, [])
  
  // ref를 통해 메서드 노출
  useImperativeHandle(ref, () => ({
    panTo: (coord) => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.getView().animate({
          center: coord,
          zoom: 16,
          duration: 500,
        })
      }
    },
    getMap: () => mapInstanceRef.current,
    getBbox: getCurrentBbox,  // bbox 조회 메서드 노출
  }), [getCurrentBbox])
  
  // 지도 초기화
  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return
    
    // 배경지도 레이어 (VWorld)
    const baseLayer = new TileLayer({
      source: new XYZ({
        url: 'https://api.vworld.kr/req/wmts/1.0.0/F1849B6C-14D6-3F57-97F7-98BBFE66CFB/Base/{z}/{y}/{x}.png',
        crossOrigin: 'anonymous',
      }),
    })
    
    // OSM 폴백
    const osmLayer = new TileLayer({
      source: new OSM(),
      visible: false,
    })
    
    // 시설물 레이어 (전주, 전선, 변압기, 도로, 건물, 철도, 하천)
    const facilitySource = new VectorSource()
    const facilityLayer = new VectorLayer({
      source: facilitySource,
      zIndex: 30,
    })
    facilityLayerRef.current = facilityLayer
    
    // 수용가 레이어
    const consumerSource = new VectorSource()
    const consumerLayer = new VectorLayer({
      source: consumerSource,
      zIndex: 100,
    })
    consumerLayerRef.current = consumerLayer
    
    // 경로 레이어
    const routeSource = new VectorSource()
    const routeLayer = new VectorLayer({
      source: routeSource,
      zIndex: 50,
    })
    routeLayerRef.current = routeLayer
    
    // 전주 레이어
    const poleSource = new VectorSource()
    const poleLayer = new VectorLayer({
      source: poleSource,
      zIndex: 80,
    })
    poleLayerRef.current = poleLayer
    
    // 지도 생성
    const map = new Map({
      target: mapRef.current,
      layers: [baseLayer, osmLayer, facilityLayer, routeLayer, poleLayer, consumerLayer],
      view: new View({
        center: fromLonLat([127.85, 36.97]), // 충주시 중심
        zoom: 14,
        minZoom: 10,
        maxZoom: 19,
      }),
      controls: defaultControls().extend([
        new ScaleLine({ units: 'metric' }),
        new ZoomSlider(),
      ]),
    })
    
    // 클릭 이벤트
    map.on('click', (evt) => {
      const coord = evt.coordinate
      onMapClick && onMapClick(coord)
    })
    
    // 마우스 이동 이벤트 (좌표 표시)
    map.on('pointermove', (evt) => {
      setMouseCoord(evt.coordinate)
    })
    
    // 지도 이동 완료 이벤트 (bbox 변경)
    map.on('moveend', () => {
      if (onViewChange) {
        const extent = map.getView().calculateExtent(map.getSize())
        onViewChange({
          minX: extent[0],
          minY: extent[1],
          maxX: extent[2],
          maxY: extent[3],
          toString: () => `${extent[0]},${extent[1]},${extent[2]},${extent[3]}`
        })
      }
    })
    
    // VWorld 로드 실패 시 OSM으로 전환
    baseLayer.getSource().on('tileloaderror', () => {
      baseLayer.setVisible(false)
      osmLayer.setVisible(true)
    })
    
    mapInstanceRef.current = map
    
    return () => {
      map.setTarget(null)
      mapInstanceRef.current = null
    }
  }, [onMapClick, onViewChange])
  
  // 수용가 위치 업데이트
  useEffect(() => {
    if (!consumerLayerRef.current) return
    
    const source = consumerLayerRef.current.getSource()
    source.clear()
    
    if (consumerCoord) {
      const feature = new Feature({
        geometry: new Point(consumerCoord),
        type: 'consumer',
      })
      
      feature.setStyle(createConsumerStyle())
      source.addFeature(feature)
      
      // 지도 이동
      mapInstanceRef.current?.getView().animate({
        center: consumerCoord,
        duration: 300,
      })
    }
  }, [consumerCoord])
  
  // 이전 result를 추적하여 줌 초기화 여부 결정
  const prevResultRef = useRef(null)
  
  // 설계 결과 업데이트
  useEffect(() => {
    if (!routeLayerRef.current || !poleLayerRef.current) return
    
    const routeSource = routeLayerRef.current.getSource()
    const poleSource = poleLayerRef.current.getSource()
    
    routeSource.clear()
    poleSource.clear()
    
    if (!result || !result.routes || result.routes.length === 0) return
    
    // 선택되지 않은 경로 먼저 그리기 (아래에 깔림)
    result.routes.forEach((route, index) => {
      if (index === selectedRouteIndex) return // 선택된 경로는 나중에
      
      // 경로 라인
      if (route.path_coordinates && route.path_coordinates.length >= 2) {
        const lineFeature = new Feature({
          geometry: new LineString(route.path_coordinates),
          routeIndex: index,
          rank: route.rank,
        })
        lineFeature.setStyle(createRouteStyle(false, index))
        routeSource.addFeature(lineFeature)
      }
      
      // 신설 전주
      if (route.new_pole_coordinates) {
        route.new_pole_coordinates.forEach((coord, poleIndex) => {
          const poleFeature = new Feature({
            geometry: new Point(coord),
            type: 'new_pole',
            routeIndex: index,
            poleIndex: poleIndex,
          })
          poleFeature.setStyle(createNewPoleStyle(false, index))
          poleSource.addFeature(poleFeature)
        })
      }
      
      // 기설 전주
      if (route.path_coordinates && route.path_coordinates.length > 0) {
        const existingPoleCoord = route.path_coordinates[route.path_coordinates.length - 1]
        const existingPoleFeature = new Feature({
          geometry: new Point(existingPoleCoord),
          type: 'existing_pole',
          routeIndex: index,
          poleId: route.start_pole_id,
        })
        existingPoleFeature.setStyle(createExistingPoleStyle(false, index))
        poleSource.addFeature(existingPoleFeature)
      }
    })
    
    // 선택된 경로 나중에 그리기 (위에 표시됨)
    const selectedRoute = result.routes[selectedRouteIndex]
    if (selectedRoute) {
      // 경로 라인
      if (selectedRoute.path_coordinates && selectedRoute.path_coordinates.length >= 2) {
        const lineFeature = new Feature({
          geometry: new LineString(selectedRoute.path_coordinates),
          routeIndex: selectedRouteIndex,
          rank: selectedRoute.rank,
        })
        lineFeature.setStyle(createRouteStyle(true, selectedRouteIndex))
        routeSource.addFeature(lineFeature)
      }
      
      // 신설 전주
      if (selectedRoute.new_pole_coordinates) {
        selectedRoute.new_pole_coordinates.forEach((coord, poleIndex) => {
          const poleFeature = new Feature({
            geometry: new Point(coord),
            type: 'new_pole',
            routeIndex: selectedRouteIndex,
            poleIndex: poleIndex,
          })
          poleFeature.setStyle(createNewPoleStyle(true, selectedRouteIndex))
          poleSource.addFeature(poleFeature)
        })
      }
      
      // 기설 전주
      if (selectedRoute.path_coordinates && selectedRoute.path_coordinates.length > 0) {
        const existingPoleCoord = selectedRoute.path_coordinates[selectedRoute.path_coordinates.length - 1]
        const existingPoleFeature = new Feature({
          geometry: new Point(existingPoleCoord),
          type: 'existing_pole',
          routeIndex: selectedRouteIndex,
          poleId: selectedRoute.start_pole_id,
        })
        existingPoleFeature.setStyle(createExistingPoleStyle(true, selectedRouteIndex))
        poleSource.addFeature(existingPoleFeature)
      }
    }
    
    // 새로운 결과일 때만 뷰 조정 (경로 선택 변경 시에는 줌 유지)
    const isNewResult = prevResultRef.current !== result
    if (isNewResult && selectedRoute?.path_coordinates?.length > 0) {
      const extent = routeSource.getExtent()
      mapInstanceRef.current?.getView().fit(extent, {
        padding: [100, 100, 100, 100],
        maxZoom: 18,
        duration: 500,
      })
    }
    prevResultRef.current = result
  }, [result, selectedRouteIndex])
  
  // 시설물 표시 업데이트
  useEffect(() => {
    if (!facilityLayerRef.current) return
    
    const source = facilityLayerRef.current.getSource()
    source.clear()
    
    if (!showFacilities || !facilities) return
    
    // 건물 표시 (가장 먼저 - 뒤에 깔리도록)
    if (facilities.buildings) {
      facilities.buildings.forEach((building) => {
        const coords = building.coordinates
        if (coords && coords.length >= 3) {
          try {
            const feature = new Feature({
              geometry: new Polygon([coords]),
              type: 'facility_building',
              id: building.id,
            })
            feature.setStyle(createBuildingStyle())
            source.addFeature(feature)
          } catch (e) {
            // 폴리곤 생성 실패 시 무시
          }
        }
      })
    }
    
    // 하천/기타영역 표시 (AI_BASE_001 - 실제로는 무벽건물/가설건물 등)
    // 현재 WFS 서버에 실제 하천 데이터가 없으므로 건물 스타일로 표시
    if (facilities.rivers) {
      facilities.rivers.forEach((river) => {
        const coords = river.coordinates
        if (coords && coords.length >= 3) {
          try {
            const feature = new Feature({
              geometry: new Polygon([coords]),
              type: 'facility_building_other',  // 기타 건물로 처리
              id: river.id,
            })
            // 건물 스타일 적용 (약간 다른 색상)
            feature.setStyle(createOtherBuildingStyle())
            source.addFeature(feature)
          } catch (e) {
            // 폴리곤 생성 실패 시 무시
          }
        }
      })
    }
    
    // 도로 표시
    if (facilities.roads) {
      facilities.roads.forEach((road) => {
        if (road.coordinates && road.coordinates.length >= 2) {
          const feature = new Feature({
            geometry: new LineString(road.coordinates),
            type: 'facility_road',
            id: road.id,
          })
          feature.setStyle(createRoadStyle())
          source.addFeature(feature)
        }
      })
    }
    
    // 철도 표시
    if (facilities.railways) {
      facilities.railways.forEach((railway) => {
        const coords = railway.coordinates
        if (coords) {
          try {
            // 철도가 폴리곤이면 외곽선으로, 선이면 그대로
            if (coords.length >= 3 && Array.isArray(coords[0])) {
              const feature = new Feature({
                geometry: new Polygon([coords]),
                type: 'facility_railway',
                id: railway.id,
              })
              feature.setStyle(createRailwayStyle())
              source.addFeature(feature)
            }
          } catch (e) {
            // 생성 실패 시 무시
          }
        }
      })
    }
    
    // 전선 표시
    if (facilities.lines) {
      facilities.lines.forEach((line) => {
        if (line.coordinates && line.coordinates.length >= 2) {
          const feature = new Feature({
            geometry: new LineString(line.coordinates),
            type: 'facility_line',
            lineId: line.id,
            lineType: line.line_type,
            phaseCode: line.phase_code,
          })
          feature.setStyle(createFacilityLineStyle(line.line_type, line.phase_code))
          source.addFeature(feature)
        }
      })
    }
    
    // 변압기 표시
    if (facilities.transformers) {
      facilities.transformers.forEach((tr) => {
        const coords = tr.coordinates
        if (coords) {
          // 좌표가 단일 점이면 Point, 배열이면 LineString
          const isPoint = !Array.isArray(coords[0])
          const feature = new Feature({
            geometry: isPoint ? new Point(coords) : new LineString(coords),
            type: 'facility_transformer',
            id: tr.id,
            capacity: tr.capacity_kva,
          })
          feature.setStyle(createTransformerStyle())
          source.addFeature(feature)
        }
      })
    }
    
    // 전주 표시 (가장 나중에 - 위에 그려지도록)
    if (facilities.poles) {
      facilities.poles.forEach((pole) => {
        const coord = pole.coordinates || pole.coord
        if (coord && coord.length === 2) {
          const feature = new Feature({
            geometry: new Point(coord),
            type: 'facility_pole',
            poleId: pole.id,
            phase: pole.phase_code,
            poleType: pole.pole_type,
          })
          feature.setStyle(createFacilityPoleStyle(pole.phase_code, pole.pole_type))
          source.addFeature(feature)
        }
      })
    }
  }, [showFacilities, facilities])
  
  return (
    <div ref={mapRef} className="w-full h-full relative">
      {/* 지도 컨트롤 버튼 */}
      <div className="absolute top-4 right-4 flex flex-col gap-2 z-10">
        {/* 현재 위치 버튼 */}
        <button
          onClick={onGoToCurrentLocation}
          className="w-10 h-10 bg-bg-secondary/90 hover:bg-bg-tertiary backdrop-blur-sm rounded-lg shadow-lg flex items-center justify-center transition-colors"
          title="현재 위치로 이동"
        >
          <svg className="w-5 h-5 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
              d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
              d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </button>
        
        {/* 확대 버튼 */}
        <button
          onClick={() => {
            const view = mapInstanceRef.current?.getView()
            if (view) view.animate({ zoom: view.getZoom() + 1, duration: 200 })
          }}
          className="w-10 h-10 bg-bg-secondary/90 hover:bg-bg-tertiary backdrop-blur-sm rounded-lg shadow-lg flex items-center justify-center transition-colors"
          title="확대"
        >
          <svg className="w-5 h-5 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </button>
        
        {/* 축소 버튼 */}
        <button
          onClick={() => {
            const view = mapInstanceRef.current?.getView()
            if (view) view.animate({ zoom: view.getZoom() - 1, duration: 200 })
          }}
          className="w-10 h-10 bg-bg-secondary/90 hover:bg-bg-tertiary backdrop-blur-sm rounded-lg shadow-lg flex items-center justify-center transition-colors"
          title="축소"
        >
          <svg className="w-5 h-5 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
          </svg>
        </button>
      </div>
      
      {/* 범례 */}
      <div className="absolute bottom-20 left-4 bg-bg-secondary/90 backdrop-blur-sm rounded-lg p-3 shadow-lg z-10 max-h-80 overflow-y-auto">
        <h4 className="text-xs font-medium text-slate-400 mb-2">범례</h4>
        <div className="space-y-1.5">
          {/* 기본 범례 */}
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 flex items-center justify-center">
              <svg className="w-3 h-3 text-red-500" viewBox="0 0 24 24" fill="currentColor">
                <polygon points="12,2 15,10 24,10 17,15 19,23 12,18 5,23 7,15 0,10 9,10" />
              </svg>
            </div>
            <span className="text-xs text-slate-300">수용가</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex gap-0.5">
              <div className="w-2 h-2 rounded-full bg-blue-500" />
              <div className="w-2 h-2 rounded-full bg-green-500" />
              <div className="w-2 h-2 rounded-full bg-amber-500" />
              <div className="w-2 h-2 rounded-full bg-violet-500" />
              <div className="w-2 h-2 rounded-full bg-pink-500" />
            </div>
            <span className="text-xs text-slate-300">신설 전주 (경로별)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-slate-500 border-2 border-slate-300" />
            <span className="text-xs text-slate-300">기설 전주</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex gap-0.5 items-center">
              <div className="w-3 h-0.5 bg-blue-500" />
              <div className="w-3 h-0.5 bg-green-500" />
              <div className="w-3 h-0.5 bg-amber-500" />
            </div>
            <span className="text-xs text-slate-300">신설 경로 (경로별)</span>
          </div>
          
          {/* 시설물 범례 */}
          {showFacilities && (
            <>
              <div className="border-t border-slate-600 my-2 pt-2">
                <span className="text-xs text-slate-500">시설물</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-amber-500 border-2 border-white" />
                <span className="text-xs text-slate-300">고압 3상 전주</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-red-500 border-2 border-white" />
                <span className="text-xs text-slate-300">고압 전주</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full bg-stone-400 border border-white" />
                <span className="text-xs text-slate-300">저압 전주</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-0.5 bg-red-500" />
                <span className="text-xs text-slate-300">고압 전선</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-0.5 bg-orange-400" />
                <span className="text-xs text-slate-300">저압 전선</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-600 border border-white" />
                <span className="text-xs text-slate-300">변압기</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-0.5 bg-slate-400" style={{ borderBottom: '2px dashed' }} />
                <span className="text-xs text-slate-300">도로</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-3 bg-amber-200/50 border border-amber-300" />
                <span className="text-xs text-slate-300">건물</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-3 bg-gray-300/30 border border-gray-400" />
                <span className="text-xs text-slate-300">기타 건물</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-0.5 bg-gray-800" style={{ borderBottom: '3px dotted' }} />
                <span className="text-xs text-slate-300">철도</span>
              </div>
            </>
          )}
        </div>
      </div>
      
      {/* 마우스 좌표 표시 (하단) */}
      <div className="absolute bottom-4 left-4 bg-bg-secondary/80 backdrop-blur-sm rounded px-2 py-1 shadow z-10">
        <div className="text-xs font-mono text-slate-400">
          {mouseCoord 
            ? `X: ${mouseCoord[0].toFixed(2)}, Y: ${mouseCoord[1].toFixed(2)}`
            : 'EPSG:3857'
          }
        </div>
      </div>
    </div>
  )
})

export default MapView

// ========== 스타일 함수들 ==========

// 수용가 스타일
function createConsumerStyle() {
  return new Style({
    image: new RegularShape({
      fill: new Fill({ color: '#ef4444' }),
      stroke: new Stroke({ color: '#ffffff', width: 2 }),
      points: 5,
      radius: 12,
      radius2: 6,
      angle: 0,
    }),
  })
}

// 경로 스타일
function createRouteStyle(isSelected, index) {
  const colors = ['#3b82f6', '#22c55e', '#f59e0b', '#8b5cf6', '#ec4899']
  const color = colors[index % colors.length]
  
  return new Style({
    stroke: new Stroke({
      color: isSelected ? color : `${color}80`,
      width: isSelected ? 4 : 2,
      lineDash: isSelected ? null : [5, 5],
    }),
  })
}

// 신설 전주 스타일 (경로별 색상 적용)
function createNewPoleStyle(isSelected, routeIndex = 0) {
  // 경로 색상과 동일하게 적용
  const colors = ['#3b82f6', '#22c55e', '#f59e0b', '#8b5cf6', '#ec4899']
  const color = colors[routeIndex % colors.length]
  
  return new Style({
    image: new CircleStyle({
      radius: isSelected ? 9 : 6,
      fill: new Fill({ color: color }),
      stroke: new Stroke({ 
        color: isSelected ? '#ffffff' : '#1e293b', 
        width: isSelected ? 3 : 2 
      }),
    }),
    // 선택된 전주에 번호 라벨 표시
    text: isSelected ? new Text({
      text: `${routeIndex + 1}`,
      offsetY: 1,
      fill: new Fill({ color: '#ffffff' }),
      font: 'bold 10px sans-serif',
    }) : null,
  })
}

// 기설 전주 스타일 (경로별 테두리 색상)
function createExistingPoleStyle(isSelected, routeIndex = 0) {
  const colors = ['#3b82f6', '#22c55e', '#f59e0b', '#8b5cf6', '#ec4899']
  const borderColor = isSelected ? colors[routeIndex % colors.length] : '#94a3b8'
  
  return new Style({
    image: new CircleStyle({
      radius: isSelected ? 12 : 7,
      fill: new Fill({ color: '#64748b' }),
      stroke: new Stroke({ 
        color: borderColor, 
        width: isSelected ? 4 : 2 
      }),
    }),
    text: isSelected ? new Text({
      text: '기설전주',
      offsetY: -20,
      fill: new Fill({ color: '#ffffff' }),
      stroke: new Stroke({ color: '#1e293b', width: 3 }),
      font: 'bold 11px sans-serif',
    }) : null,
  })
}

// 시설물 전주 스타일
function createFacilityPoleStyle(phaseCode, poleType) {
  // 3상 여부 확인: CBA (3상 코드) 또는 "3" 문자열
  const is3Phase = phaseCode === 'CBA' || phaseCode === '3' || phaseCode === 3
  // 고압 여부: H = 고압
  const isHighVoltage = poleType === 'H'
  
  // 고압 3상: 주황색, 고압 단상: 빨간색, 저압: 회색
  let fillColor, radius
  if (isHighVoltage && is3Phase) {
    fillColor = '#f59e0b'    // 주황색 (고압 3상)
    radius = 8
  } else if (isHighVoltage) {
    fillColor = '#ef4444'    // 빨간색 (고압 단상)
    radius = 7
  } else {
    fillColor = '#78716c'    // 회색 (저압/기타)
    radius = 5
  }
  
  return new Style({
    image: new CircleStyle({
      radius: radius,
      fill: new Fill({ color: fillColor }),
      stroke: new Stroke({ color: '#ffffff', width: 2 }),
    }),
  })
}

// 시설물 전선 스타일
function createFacilityLineStyle(lineType, phaseCode) {
  const isHighVoltage = lineType === 'HV' || lineType?.includes('고압')
  const is3Phase = phaseCode === 'CBA' || phaseCode === '3' || phaseCode === 3
  
  // 고압 3상: 주황색, 고압: 빨간색, 저압: 주황색
  let color, width
  if (isHighVoltage && is3Phase) {
    color = 'rgba(245, 158, 11, 0.9)'  // 주황색 (고압 3상)
    width = 4
  } else if (isHighVoltage) {
    color = 'rgba(239, 68, 68, 0.8)'   // 빨간색 (고압)
    width = 3
  } else {
    color = 'rgba(251, 146, 60, 0.7)'  // 주황색 (저압)
    width = 2
  }
  
  return new Style({
    stroke: new Stroke({
      color: color,
      width: width,
    }),
  })
}

// 변압기 스타일 (사각형, 녹색)
function createTransformerStyle() {
  return new Style({
    image: new RegularShape({
      fill: new Fill({ color: '#16a34a' }),  // 녹색
      stroke: new Stroke({ color: '#ffffff', width: 2 }),
      points: 4,
      radius: 8,
      angle: Math.PI / 4,  // 45도 회전하여 다이아몬드 형태
    }),
  })
}

// 도로 스타일 (회색 점선)
function createRoadStyle() {
  return new Style({
    stroke: new Stroke({
      color: 'rgba(156, 163, 175, 0.7)',  // 회색
      width: 2,
      lineDash: [8, 4],  // 점선
    }),
  })
}

// 건물 스타일 (연한 갈색 반투명 폴리곤)
function createBuildingStyle() {
  return new Style({
    fill: new Fill({ color: 'rgba(217, 173, 100, 0.3)' }),  // 연한 갈색
    stroke: new Stroke({ color: 'rgba(180, 140, 80, 0.6)', width: 1 }),
  })
}

// 기타 건물 스타일 (무벽건물, 가설건물 등 - 연한 회색)
function createOtherBuildingStyle() {
  return new Style({
    fill: new Fill({ color: 'rgba(156, 163, 175, 0.25)' }),  // 연한 회색
    stroke: new Stroke({ color: 'rgba(107, 114, 128, 0.5)', width: 1 }),
  })
}

// 하천 스타일 (실제 하천 데이터용 - 현재 미사용)
function createRiverStyle() {
  return new Style({
    fill: new Fill({ color: 'rgba(147, 197, 253, 0.4)' }),  // 연한 파란색
    stroke: new Stroke({ color: 'rgba(96, 165, 250, 0.7)', width: 1 }),
  })
}

// 철도 스타일 (검정 굵은 점선)
function createRailwayStyle() {
  return new Style({
    fill: new Fill({ color: 'rgba(75, 85, 99, 0.3)' }),  // 연한 회색
    stroke: new Stroke({
      color: 'rgba(31, 41, 55, 0.8)',  // 어두운 회색
      width: 3,
      lineDash: [4, 4],  // 점선
    }),
  })
}
