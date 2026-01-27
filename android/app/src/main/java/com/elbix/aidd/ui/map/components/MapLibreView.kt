package com.elbix.aidd.ui.map.components

import android.graphics.Color
import android.util.Log
import androidx.compose.foundation.layout.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import com.elbix.aidd.domain.model.*
import com.elbix.aidd.ui.main.LayerVisibility
import com.elbix.aidd.util.CoordinateUtils
import org.osmdroid.config.Configuration
import org.osmdroid.tileprovider.tilesource.TileSourceFactory
import org.osmdroid.util.GeoPoint
import org.osmdroid.views.MapView
import org.osmdroid.views.overlay.Marker
import org.osmdroid.views.overlay.Polyline

/**
 * OSMDroid 기반 지도 Composable
 * - OpenStreetMap 타일 사용 (무료)
 * - 시설물 표시 (전주, 전선, 변압기)
 * - 설계 결과 표시 (경로, 신설 전주, 수용가)
 * - 지도 클릭으로 좌표 선택
 * - 외부에서 지도 위치 제어 가능
 */
@Composable
fun MapLibreView(
    modifier: Modifier = Modifier,
    facilities: FacilitiesData?,
    layerVisibility: LayerVisibility,
    selectedCoordinate: Coordinate?,
    moveToCoordinate: Coordinate? = null,  // 외부에서 이동 요청
    designResult: DesignResult? = null,     // 설계 결과
    selectedRouteIndex: Int = 0,            // 선택된 경로 인덱스
    onMapClick: (Coordinate) -> Unit,
    onMapLongClick: (Coordinate) -> Unit,
    onCameraMove: (BoundingBox) -> Unit,
    onMoveCompleted: () -> Unit = {}  // 이동 완료 콜백
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    
    // OSMDroid 설정 확인
    LaunchedEffect(Unit) {
        try {
            // User-Agent가 설정되어 있지 않으면 설정
            if (Configuration.getInstance().userAgentValue.isNullOrEmpty()) {
                Configuration.getInstance().userAgentValue = context.packageName
            }
        } catch (e: Exception) {
            Log.e("MapView", "Error configuring OSMDroid", e)
        }
    }
    
    // MapView 참조
    var mapView by remember { mutableStateOf<MapView?>(null) }
    
    // 선택된 좌표 마커
    var selectedMarker by remember { mutableStateOf<Marker?>(null) }
    
    // 시설물 오버레이 업데이트
    LaunchedEffect(facilities, layerVisibility, mapView) {
        mapView?.let { map ->
            updateFacilitiesOverlays(map, facilities, layerVisibility)
        }
    }
    
    // 선택된 좌표 마커 업데이트
    LaunchedEffect(selectedCoordinate, mapView) {
        mapView?.let { map ->
            // 기존 마커 제거
            selectedMarker?.let { map.overlays.remove(it) }
            
            // 새 마커 추가
            selectedCoordinate?.let { coord ->
                val (lat, lng) = CoordinateUtils.epsg3857ToWgs84(coord.x, coord.y)
                val marker = Marker(map).apply {
                    position = GeoPoint(lat, lng)
                    setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_BOTTOM)
                    title = "선택된 위치"
                    snippet = "X: ${String.format("%.2f", coord.x)}\nY: ${String.format("%.2f", coord.y)}"
                }
                map.overlays.add(marker)
                selectedMarker = marker
            }
            
            map.invalidate()
        }
    }
    
    // 외부에서 지도 이동 요청 처리
    LaunchedEffect(moveToCoordinate, mapView) {
        moveToCoordinate?.let { coord ->
            mapView?.let { map ->
                try {
                    val (lat, lng) = CoordinateUtils.epsg3857ToWgs84(coord.x, coord.y)
                    map.controller.animateTo(GeoPoint(lat, lng))
                    map.controller.setZoom(17.0)
                    
                    // 이동 후 BBox 업데이트
                    map.postDelayed({
                        reportBoundingBox(map, onCameraMove)
                        onMoveCompleted()
                    }, 500)
                    
                    Log.d("MapView", "Moved to coordinate: lat=$lat, lng=$lng")
                } catch (e: Exception) {
                    Log.e("MapView", "Error moving to coordinate", e)
                }
            }
        }
    }
    
    // 설계 결과 오버레이 업데이트
    LaunchedEffect(designResult, selectedRouteIndex, mapView) {
        mapView?.let { map ->
            updateDesignResultOverlays(map, designResult, selectedRouteIndex)
        }
    }
    
    // 생명주기 관리
    DisposableEffect(lifecycleOwner) {
        val observer = LifecycleEventObserver { _, event ->
            when (event) {
                Lifecycle.Event.ON_RESUME -> mapView?.onResume()
                Lifecycle.Event.ON_PAUSE -> mapView?.onPause()
                else -> {}
            }
        }
        lifecycleOwner.lifecycle.addObserver(observer)
        onDispose {
            lifecycleOwner.lifecycle.removeObserver(observer)
        }
    }
    
    AndroidView(
        modifier = modifier.fillMaxSize(),
        factory = { ctx ->
            MapView(ctx).apply {
                try {
                    mapView = this
                    
                    // 타일 소스 설정 (OpenStreetMap)
                    setTileSource(TileSourceFactory.MAPNIK)
                    
                    // 멀티터치 줌 활성화
                    setMultiTouchControls(true)
                    
                    // 내장 줌 컨트롤
                    @Suppress("DEPRECATION")
                    setBuiltInZoomControls(true)
                    
                    // 초기 위치 (서울 시청)
                    controller.setZoom(CoordinateUtils.DEFAULT_ZOOM)
                    controller.setCenter(
                        GeoPoint(CoordinateUtils.SeoulCityHall.LAT, CoordinateUtils.SeoulCityHall.LNG)
                    )
                    
                    // 탭 이벤트 처리를 위한 오버레이 추가
                    overlays.add(object : org.osmdroid.views.overlay.Overlay() {
                        override fun onSingleTapConfirmed(
                            e: android.view.MotionEvent?,
                            mapView: MapView?
                        ): Boolean {
                            try {
                                e?.let { event ->
                                    mapView?.let { map ->
                                        val projection = map.projection
                                        val geoPoint = projection.fromPixels(
                                            event.x.toInt(),
                                            event.y.toInt()
                                        ) as GeoPoint
                                        
                                        val (x, y) = CoordinateUtils.wgs84ToEpsg3857(
                                            geoPoint.latitude,
                                            geoPoint.longitude
                                        )
                                        onMapClick(Coordinate(x, y))
                                    }
                                }
                            } catch (e: Exception) {
                                Log.e("MapView", "Error on tap", e)
                            }
                            return true
                        }
                        
                        override fun onLongPress(
                            e: android.view.MotionEvent?,
                            mapView: MapView?
                        ): Boolean {
                            try {
                                e?.let { event ->
                                    mapView?.let { map ->
                                        val projection = map.projection
                                        val geoPoint = projection.fromPixels(
                                            event.x.toInt(),
                                            event.y.toInt()
                                        ) as GeoPoint
                                        
                                        val (x, y) = CoordinateUtils.wgs84ToEpsg3857(
                                            geoPoint.latitude,
                                            geoPoint.longitude
                                        )
                                        onMapLongClick(Coordinate(x, y))
                                    }
                                }
                            } catch (e: Exception) {
                                Log.e("MapView", "Error on long press", e)
                            }
                            return true
                        }
                    })
                    
                    // 카메라 이동 완료 이벤트
                    addOnFirstLayoutListener { _, _, _, _, _ ->
                        reportBoundingBox(this, onCameraMove)
                    }
                    
                    setOnTouchListener { _, _ ->
                        // 터치 후 BBox 업데이트
                        postDelayed({
                            reportBoundingBox(this, onCameraMove)
                        }, 500)
                        false
                    }
                    
                    Log.d("MapView", "MapView initialized successfully")
                } catch (e: Exception) {
                    Log.e("MapView", "Error initializing MapView", e)
                }
            }
        }
    )
}

/**
 * 현재 화면의 BoundingBox 전달
 */
private fun reportBoundingBox(mapView: MapView, onCameraMove: (BoundingBox) -> Unit) {
    try {
        val bounds = mapView.boundingBox
        val bbox = CoordinateUtils.boundingBoxFromWgs84(
            swLat = bounds.latSouth,
            swLng = bounds.lonWest,
            neLat = bounds.latNorth,
            neLng = bounds.lonEast
        )
        onCameraMove(bbox)
    } catch (e: Exception) {
        Log.e("MapView", "Error getting bounds", e)
    }
}

/**
 * 시설물 오버레이 업데이트
 */
private fun updateFacilitiesOverlays(
    mapView: MapView,
    facilities: FacilitiesData?,
    layerVisibility: LayerVisibility
) {
    if (facilities == null) return
    
    try {
        // 기존 시설물 오버레이 제거 (선택 마커 제외)
        mapView.overlays.removeAll { overlay ->
            overlay is Marker && overlay.id?.startsWith("facility_") == true
        }
        mapView.overlays.removeAll { it is Polyline }
        
        // 전주 마커 추가
        if (layerVisibility.poles) {
            facilities.poles.forEach { pole ->
                val (lat, lng) = CoordinateUtils.epsg3857ToWgs84(pole.coordinate.x, pole.coordinate.y)
                val marker = Marker(mapView).apply {
                    id = "facility_pole_${pole.id}"
                    position = GeoPoint(lat, lng)
                    setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_CENTER)
                    title = "전주 ${pole.id}"
                    snippet = if (pole.isHighVoltage) "고압" else "저압"
                    // 색상은 기본 아이콘 사용
                }
                mapView.overlays.add(marker)
            }
        }
        
        // 전선 라인 추가
        if (layerVisibility.lines) {
            facilities.lines.filter { it.coordinates.size >= 2 }.forEach { line ->
                val polyline = Polyline().apply {
                    outlinePaint.color = android.graphics.Color.parseColor("#2196F3")
                    outlinePaint.strokeWidth = 3f
                    
                    val points = line.coordinates.map { coord ->
                        val (lat, lng) = CoordinateUtils.epsg3857ToWgs84(coord.x, coord.y)
                        GeoPoint(lat, lng)
                    }
                    setPoints(points)
                }
                mapView.overlays.add(polyline)
            }
        }
        
        // 변압기 마커 추가
        if (layerVisibility.transformers) {
            facilities.transformers.forEach { transformer ->
                val (lat, lng) = CoordinateUtils.epsg3857ToWgs84(
                    transformer.coordinate.x,
                    transformer.coordinate.y
                )
                val marker = Marker(mapView).apply {
                    id = "facility_transformer_${transformer.id}"
                    position = GeoPoint(lat, lng)
                    setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_CENTER)
                    title = "변압기"
                    snippet = transformer.formattedCapacity
                }
                mapView.overlays.add(marker)
            }
        }
        
        mapView.invalidate()
        Log.d("MapView", "Facilities updated: poles=${facilities.poles.size}, lines=${facilities.lines.size}")
    } catch (e: Exception) {
        Log.e("MapView", "Error updating facilities", e)
    }
}

/**
 * 설계 결과 오버레이 업데이트
 * - 경로 라인 (색상별로 구분)
 * - 신설 전주 마커
 * - 시작 전주 마커
 * - 수용가 마커
 */
private fun updateDesignResultOverlays(
    mapView: MapView,
    result: DesignResult?,
    selectedRouteIndex: Int
) {
    try {
        // 기존 설계 오버레이 제거
        mapView.overlays.removeAll { overlay ->
            (overlay is Marker && overlay.id?.startsWith("design_") == true) ||
            (overlay is Polyline && overlay.id?.startsWith("design_") == true)
        }
        
        if (result == null || result.routes.isEmpty()) {
            mapView.invalidate()
            return
        }
        
        // 경로 색상 (순위별)
        val routeColors = listOf(
            Color.parseColor("#4CAF50"),  // 녹색 (1순위)
            Color.parseColor("#2196F3"),  // 파란색 (2순위)
            Color.parseColor("#FF9800"),  // 주황색 (3순위)
            Color.parseColor("#9C27B0"),  // 보라색 (4순위)
            Color.parseColor("#F44336")   // 빨간색 (5순위)
        )
        
        // 선택된 경로 정보
        val selectedRoute = result.routes.getOrNull(selectedRouteIndex)
        
        // 모든 경로 표시 (선택된 경로는 굵게)
        result.routes.forEachIndexed { index, route ->
            val color = routeColors.getOrElse(index) { Color.GRAY }
            val isSelected = index == selectedRouteIndex
            
            // 경로 라인
            if (route.pathCoordinates.size >= 2) {
                val polyline = Polyline().apply {
                    id = "design_route_$index"
                    outlinePaint.color = color
                    outlinePaint.strokeWidth = if (isSelected) 8f else 4f
                    outlinePaint.alpha = if (isSelected) 255 else 150
                    
                    val points = route.pathCoordinates.map { coord ->
                        val (lat, lng) = CoordinateUtils.epsg3857ToWgs84(coord.x, coord.y)
                        GeoPoint(lat, lng)
                    }
                    setPoints(points)
                }
                mapView.overlays.add(polyline)
            }
        }
        
        // 선택된 경로의 상세 정보 표시
        selectedRoute?.let { route ->
            // 시작 전주 마커 (파란색)
            val (startLat, startLng) = CoordinateUtils.epsg3857ToWgs84(
                route.startPoleCoord.x,
                route.startPoleCoord.y
            )
            val startMarker = Marker(mapView).apply {
                id = "design_start_pole"
                position = GeoPoint(startLat, startLng)
                setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_CENTER)
                title = "시작 전주"
                snippet = route.startPoleId
            }
            mapView.overlays.add(startMarker)
            
            // 신설 전주 마커 (주황색)
            route.newPoleCoordinates.forEachIndexed { poleIndex, coord ->
                val (lat, lng) = CoordinateUtils.epsg3857ToWgs84(coord.x, coord.y)
                val marker = Marker(mapView).apply {
                    id = "design_new_pole_$poleIndex"
                    position = GeoPoint(lat, lng)
                    setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_CENTER)
                    title = "신설 전주 ${poleIndex + 1}"
                    snippet = route.poleSpec ?: ""
                }
                mapView.overlays.add(marker)
            }
        }
        
        // 수용가 마커 (빨간색)
        val (consumerLat, consumerLng) = CoordinateUtils.epsg3857ToWgs84(
            result.consumerCoord.x,
            result.consumerCoord.y
        )
        val consumerMarker = Marker(mapView).apply {
            id = "design_consumer"
            position = GeoPoint(consumerLat, consumerLng)
            setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_BOTTOM)
            title = "수용가 (신청 위치)"
            snippet = "X: ${String.format("%.2f", result.consumerCoord.x)}\nY: ${String.format("%.2f", result.consumerCoord.y)}"
        }
        mapView.overlays.add(consumerMarker)
        
        mapView.invalidate()
        Log.d("MapView", "Design result updated: ${result.routes.size} routes, selected=$selectedRouteIndex")
    } catch (e: Exception) {
        Log.e("MapView", "Error updating design result", e)
    }
}
