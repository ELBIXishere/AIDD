package com.elbix.aidd.util

import com.elbix.aidd.domain.model.BoundingBox
import com.elbix.aidd.domain.model.Coordinate
import kotlin.math.*

/**
 * 좌표 변환 유틸리티
 * - EPSG:3857 (Web Mercator) ↔ WGS84 (위도/경도) 변환
 * - MapLibre는 WGS84를 사용하고, 백엔드 API는 EPSG:3857을 사용
 */
object CoordinateUtils {
    
    // Web Mercator 상수 (지구 반지름 * π)
    private const val EARTH_RADIUS_METERS = 6378137.0
    private const val MAX_EXTENT = EARTH_RADIUS_METERS * PI  // 20037508.34...
    
    /**
     * EPSG:3857 (Web Mercator) → WGS84 (위도/경도) 변환
     * 
     * @param x X 좌표 (meters)
     * @param y Y 좌표 (meters)
     * @return Pair(latitude, longitude)
     */
    fun epsg3857ToWgs84(x: Double, y: Double): Pair<Double, Double> {
        // X → 경도 (Longitude)
        val lng = (x / MAX_EXTENT) * 180.0
        
        // Y → 위도 (Latitude)
        val lat = Math.toDegrees(
            atan(exp((y / MAX_EXTENT) * PI)) * 2.0 - PI / 2.0
        )
        
        return Pair(lat, lng)
    }
    
    /**
     * WGS84 (위도/경도) → EPSG:3857 (Web Mercator) 변환
     * 
     * @param lat 위도 (Latitude)
     * @param lng 경도 (Longitude)
     * @return Pair(x, y) in meters
     */
    fun wgs84ToEpsg3857(lat: Double, lng: Double): Pair<Double, Double> {
        // 경도 → X
        val x = lng * MAX_EXTENT / 180.0
        
        // 위도 → Y
        val latRad = Math.toRadians(lat)
        val y = ln(tan(PI / 4.0 + latRad / 2.0)) * EARTH_RADIUS_METERS
        
        return Pair(x, y)
    }
    
    /**
     * Coordinate (EPSG:3857) → WGS84 (lat, lng) 변환
     */
    fun Coordinate.toLatLng(): Pair<Double, Double> {
        return epsg3857ToWgs84(this.x, this.y)
    }
    
    /**
     * WGS84 좌표로부터 Coordinate (EPSG:3857) 생성
     */
    fun coordinateFromLatLng(lat: Double, lng: Double): Coordinate {
        val (x, y) = wgs84ToEpsg3857(lat, lng)
        return Coordinate(x, y)
    }
    
    /**
     * BoundingBox (EPSG:3857) → WGS84 BoundingBox 변환
     * 
     * @return Pair(southWest(lat, lng), northEast(lat, lng))
     */
    fun BoundingBox.toWgs84Bounds(): Pair<Pair<Double, Double>, Pair<Double, Double>> {
        val sw = epsg3857ToWgs84(this.minX, this.minY)
        val ne = epsg3857ToWgs84(this.maxX, this.maxY)
        return Pair(sw, ne)
    }
    
    /**
     * WGS84 BoundingBox로부터 EPSG:3857 BoundingBox 생성
     */
    fun boundingBoxFromWgs84(
        swLat: Double, swLng: Double,
        neLat: Double, neLng: Double
    ): BoundingBox {
        val (minX, minY) = wgs84ToEpsg3857(swLat, swLng)
        val (maxX, maxY) = wgs84ToEpsg3857(neLat, neLng)
        return BoundingBox(minX, minY, maxX, maxY)
    }
    
    /**
     * 서울 시청 좌표 (기본 위치)
     */
    object SeoulCityHall {
        // WGS84
        const val LAT = 37.5665
        const val LNG = 126.9780
        
        // EPSG:3857
        val EPSG3857: Coordinate by lazy {
            coordinateFromLatLng(LAT, LNG)
        }
    }
    
    /**
     * 테스트 좌표 목록
     * - 설계 테스트를 위한 미리 정의된 좌표 (웹 프로젝트와 동일)
     */
    object TestCoordinates {
        // 충주시 연수동 1
        val CHUNGJU_YEONSU_1 = Coordinate(14242500.63, 4437638.69)
        const val CHUNGJU_YEONSU_1_NAME = "충주 연수동1"
        
        // 충주시 연수동 2
        val CHUNGJU_YEONSU_2 = Coordinate(14242910.96, 4437665.32)
        const val CHUNGJU_YEONSU_2_NAME = "충주 연수동2"
        
        // 충주시 안림동
        val CHUNGJU_ANRIM = Coordinate(14243659.27, 4436489.88)
        const val CHUNGJU_ANRIM_NAME = "충주 안림동"
        
        // 테스트 좌표 리스트
        val ALL = listOf(
            Pair(CHUNGJU_YEONSU_1_NAME, CHUNGJU_YEONSU_1),
            Pair(CHUNGJU_YEONSU_2_NAME, CHUNGJU_YEONSU_2),
            Pair(CHUNGJU_ANRIM_NAME, CHUNGJU_ANRIM)
        )
    }
    
    /**
     * 한국 기본 줌 레벨
     */
    const val DEFAULT_ZOOM = 15.0
    const val MIN_ZOOM = 5.0
    const val MAX_ZOOM = 18.0
}
