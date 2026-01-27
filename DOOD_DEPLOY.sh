#!/bin/bash
# DooD (Docker-out-of-Docker) 방식 배포 스크립트

set -e

echo "=========================================="
echo "  ELBIX AIDD 배포 (DooD 방식)"
echo "  도메인: stlogic.aidd.co.kr"
echo "=========================================="
echo ""

# 환경 변수 로드
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ 환경 변수 로드 완료"
else
    echo "❌ .env 파일이 없습니다."
    exit 1
fi

# Docker 소켓 확인
if [ ! -S /var/run/docker.sock ]; then
    echo "❌ Docker 소켓을 찾을 수 없습니다."
    echo "컨테이너 실행 시 -v /var/run/docker.sock:/var/run/docker.sock 옵션이 필요합니다."
    exit 1
fi

echo "✅ Docker 소켓 확인: /var/run/docker.sock"
echo ""

# Docker 연결 테스트
if ! docker ps > /dev/null 2>&1; then
    echo "⚠️  Docker 데몬에 연결할 수 없습니다."
    echo "호스트의 Docker 소켓 권한을 확인하세요."
    echo ""
    echo "해결 방법:"
    echo "1. 컨테이너를 docker 그룹으로 실행"
    echo "2. 또는 호스트에서: sudo chmod 666 /var/run/docker.sock"
    exit 1
fi

echo "✅ Docker 연결 확인 완료"
echo ""

# Docker Compose로 빌드 및 실행
echo "🔨 Docker 이미지 빌드 및 컨테이너 시작..."
docker compose -f docker-compose.yml up -d --build

echo ""
echo "⏳ 컨테이너 시작 대기 중..."
sleep 5

# 상태 확인
echo ""
echo "📊 컨테이너 상태:"
docker compose ps

echo ""
echo "📝 최근 로그:"
docker compose logs --tail=10

echo ""
echo "=========================================="
echo "✅ 배포 완료!"
echo "=========================================="
echo ""
echo "🌐 접속 URL:"
echo "   HTTP:  http://stlogic.aidd.co.kr"
echo "   HTTPS: https://stlogic.aidd.co.kr (SSL 설정 후)"
echo ""
