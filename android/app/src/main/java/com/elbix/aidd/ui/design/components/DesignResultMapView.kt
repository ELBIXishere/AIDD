package com.elbix.aidd.ui.design.components

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
import com.elbix.aidd.util.CoordinateUtils
import org.osmdroid.config.Configuration
import org.osmdroid.tileprovider.tilesource.TileSourceFactory
import org.osmdroid.util.BoundingBox as OsmBoundingBox
import org.osmdroid.util.GeoPoint
import org.osmdroid.views.MapView
import org.osmdroid.views.overlay.Marker
import org.osmdroid.views.overlay.Polyline

/**
 * 설계 결과 지도 뷰 (OSMDroid 기반)
 * - 선택된 경로 표시
 * - 수용가 위치 마커
 * - 기설/신설 전주 마커
 * - 자동 카메라 피팅
 */
@Composable
fun DesignResultMapView(
    modifier: Modifier = Modifier,
    result: DesignResult,
    selectedRouteIndex: Int,
    onMapReady: () -> Unit = {}
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    
    // OSMDroid 설정 확인
    LaunchedEffect(Unit) {
        try {
            if (Configuration.getInstance().userAgentValue.isNullOrEmpty()) {
                Configuration.getInstance().userAgentValue = context.packageName
            }
        } catch (e: Exception) {
            Log.e("DesignResultMapView", "Error configuring OSMDroid", e)
        }
    }
    
    // MapView 참조
    var mapView by remember { mutableStateOf<MapView?>(null) }
    
    // 경로 또는 선택 인덱스 변경 시 지도 업데이트
    LaunchedEffect(selectedRouteIndex, mapView) {
        mapView?.let { map ->
            updateRouteDisplay(map, result, selectedRouteIndex)
            fitCameraToRoute(map, result, selectedRouteIndex)
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
                    
                    // 초기 위치 (경로에 맞게 피팅됨)
                    controller.setZoom(CoordinateUtils.DEFAULT_ZOOM)
                    
                    // 경로 표시
                    post {
                        try {
                            updateRouteDisplay(this, result, selectedRouteIndex)
                            fitCameraToRoute(this, result, selectedRouteIndex)
                            onMapReady()
                        } catch (e: Exception) {
                            Log.e("DesignResultMapView", "Error updating route", e)
                        }
                    }
                    
                    Log.d("DesignResultMapView", "MapView initialized successfully")
                } catch (e: Exception) {
                    Log.e("DesignResultMapView", "Error initializing MapView", e)
                }
            }
        }
    )
}

/**
 * 경로 표시 업데이트
 */
private fun updateRouteDisplay(
    mapView: MapView,
    result: DesignResult,
    selectedRouteIndex: Int
) {
    val selectedRoute = result.routes.getOrNull(selectedRouteIndex) ?: return
    
    try {
        // 기존 오버레이 제거
        mapView.overlays.clear()
        
        // 경로 색상 (순위별)
        val routeColor = getRouteColor(selectedRoute.rank)
        
        // 경로 라인 추가
        if (selectedRoute.pathCoordinates.size >= 2) {
            val polyline = Polyline().apply {
                outlinePaint.color = routeColor
                outlinePaint.strokeWidth = 6f
                
                val points = selectedRoute.pathCoordinates.map { coord ->
                    val (lat, lng) = CoordinateUtils.epsg3857ToWgs84(coord.x, coord.y)
                    GeoPoint(lat, lng)
                }
                setPoints(points)
            }
            mapView.overlays.add(polyline)
        }
        
        // 시작 전주 마커 (기설 전주)
        val (startLat, startLng) = CoordinateUtils.epsg3857ToWgs84(
            selectedRoute.startPoleCoord.x,
            selectedRoute.startPoleCoord.y
        )
        val startPoleMarker = Marker(mapView).apply {
            position = GeoPoint(startLat, startLng)
            setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_CENTER)
            title = "시작 전주"
            snippet = selectedRoute.startPoleId
        }
        mapView.overlays.add(startPoleMarker)
        
        // 신설 전주 마커
        selectedRoute.newPoleCoordinates.forEachIndexed { index, coord ->
            val (lat, lng) = CoordinateUtils.epsg3857ToWgs84(coord.x, coord.y)
            val marker = Marker(mapView).apply {
                position = GeoPoint(lat, lng)
                setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_CENTER)
                title = "신설 전주 ${index + 1}"
            }
            mapView.overlays.add(marker)
        }
        
        // 수용가 마커
        val (consumerLat, consumerLng) = CoordinateUtils.epsg3857ToWgs84(
            result.consumerCoord.x,
            result.consumerCoord.y
        )
        val consumerMarker = Marker(mapView).apply {
            position = GeoPoint(consumerLat, consumerLng)
            setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_BOTTOM)
            title = "수용가"
            snippet = "목표 위치"
        }
        mapView.overlays.add(consumerMarker)
        
        mapView.invalidate()
        Log.d("DesignResultMapView", "Route ${selectedRoute.rank} displayed")
    } catch (e: Exception) {
        Log.e("DesignResultMapView", "Error updating route display", e)
    }
}

/**
 * 카메라를 경로에 맞게 피팅
 */
private fun fitCameraToRoute(
    mapView: MapView,
    result: DesignResult,
    selectedRouteIndex: Int
) {
    val selectedRoute = result.routes.getOrNull(selectedRouteIndex) ?: return
    
    try {
        // 모든 좌표 수집
        val allCoords = mutableListOf<Coordinate>()
        allCoords.addAll(selectedRoute.pathCoordinates)
        allCoords.add(result.consumerCoord)
        allCoords.addAll(selectedRoute.newPoleCoordinates)
        
        if (allCoords.isEmpty()) return
        
        // 경계 계산
        var minLat = Double.MAX_VALUE
        var maxLat = Double.MIN_VALUE
        var minLng = Double.MAX_VALUE
        var maxLng = Double.MIN_VALUE
        
        allCoords.forEach { coord ->
            val (lat, lng) = CoordinateUtils.epsg3857ToWgs84(coord.x, coord.y)
            minLat = minOf(minLat, lat)
            maxLat = maxOf(maxLat, lat)
            minLng = minOf(minLng, lng)
            maxLng = maxOf(maxLng, lng)
        }
        
        // 패딩 추가
        val latPadding = (maxLat - minLat) * 0.1
        val lngPadding = (maxLng - minLng) * 0.1
        
        val boundingBox = OsmBoundingBox(
            maxLat + latPadding,
            maxLng + lngPadding,
            minLat - latPadding,
            minLng - lngPadding
        )
        
        mapView.zoomToBoundingBox(boundingBox, true, 50)
        
        Log.d("DesignResultMapView", "Camera fitted to route ${selectedRoute.rank}")
    } catch (e: Exception) {
        Log.e("DesignResultMapView", "Error fitting camera", e)
    }
}

/**
 * 순위별 경로 색상
 */
private fun getRouteColor(rank: Int): Int {
    return when (rank) {
        1 -> Color.parseColor("#4CAF50")  // 초록
        2 -> Color.parseColor("#2196F3")  // 파랑
        3 -> Color.parseColor("#FF9800")  // 주황
        4 -> Color.parseColor("#9C27B0")  // 보라
        else -> Color.parseColor("#607D8B")  // 회색
    }
}
