"""
ELBIX AIDD API 테스트
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """헬스 체크 엔드포인트 테스트"""
    
    def test_root_endpoint(self):
        """루트 엔드포인트 테스트"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["service"] == "ELBIX AIDD"
        assert data["status"] == "running"
    
    def test_health_endpoint(self):
        """헬스 체크 엔드포인트 테스트"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_design_status_endpoint(self):
        """설계 서비스 상태 엔드포인트 테스트"""
        response = client.get("/api/v1/design/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["service"] == "design"
        assert data["status"] == "available"
        assert data["max_distance_limit"] == 400.0


class TestDesignRequest:
    """설계 요청 테스트"""
    
    def test_design_request_validation(self):
        """요청 검증 테스트"""
        # 유효한 요청
        valid_request = {
            "code": "coord",
            "coord": "14241940.817790061,4437601.6755945515",
            "phase_code": "3"
        }
        
        # 좌표 형식 오류
        invalid_coord_request = {
            "code": "coord",
            "coord": "invalid_coord",
            "phase_code": "3"
        }
        
        # 상 코드 오류
        invalid_phase_request = {
            "code": "coord",
            "coord": "14241940.817790061,4437601.6755945515",
            "phase_code": "5"
        }
        
        # 유효한 요청은 400이 아니어야 함 (WFS 연결 실패로 500일 수 있음)
        response = client.post("/api/v1/design", json=valid_request)
        # 실제 WFS 서버 없이는 500 에러 예상
        assert response.status_code in [200, 500]
        
        # 잘못된 좌표는 422 에러
        response = client.post("/api/v1/design", json=invalid_coord_request)
        assert response.status_code == 422
        
        # 잘못된 상 코드는 422 에러
        response = client.post("/api/v1/design", json=invalid_phase_request)
        assert response.status_code == 422


class TestCoordinateUtils:
    """좌표 유틸리티 테스트"""
    
    def test_calculate_distance(self):
        """거리 계산 테스트"""
        from app.utils.coordinate import calculate_distance
        
        # 동일 점
        assert calculate_distance(0, 0, 0, 0) == 0.0
        
        # 3-4-5 삼각형
        assert abs(calculate_distance(0, 0, 3, 4) - 5.0) < 0.001
        
        # 수평 거리
        assert abs(calculate_distance(0, 0, 100, 0) - 100.0) < 0.001
    
    def test_calculate_bbox(self):
        """BBox 계산 테스트"""
        from app.utils.coordinate import calculate_bbox
        
        bbox = calculate_bbox(1000, 1000, 400)
        assert bbox == (800, 800, 1200, 1200)
        
        # 기본 크기 (400m)
        bbox = calculate_bbox(0, 0)
        assert bbox == (-200, -200, 200, 200)


class TestGeometryUtils:
    """기하학 유틸리티 테스트"""
    
    def test_point_to_line_distance(self):
        """점-선 거리 테스트"""
        from app.utils.geometry import point_to_line_distance
        
        # 수평선에서의 거리
        line = [(0, 0), (10, 0)]
        assert abs(point_to_line_distance((5, 5), line) - 5.0) < 0.001
        
        # 선 위의 점
        assert point_to_line_distance((5, 0), line) < 0.001
    
    def test_interpolate_points_on_line(self):
        """선 위 점 배치 테스트"""
        from app.utils.geometry import interpolate_points_on_line
        
        line = [(0, 0), (100, 0)]
        points = interpolate_points_on_line(line, 40)
        
        # 0, 40, 80 위치에 점
        assert len(points) == 3
        assert abs(points[0][0] - 0) < 0.001
        assert abs(points[1][0] - 40) < 0.001
        assert abs(points[2][0] - 80) < 0.001
    
    def test_calculate_angle(self):
        """각도 계산 테스트"""
        from app.utils.geometry import calculate_angle
        
        # 직선 (180도)
        assert abs(calculate_angle((0, 0), (5, 0), (10, 0)) - 180.0) < 0.001
        
        # 직각 (90도)
        assert abs(calculate_angle((0, 0), (0, 5), (5, 5)) - 90.0) < 0.001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
