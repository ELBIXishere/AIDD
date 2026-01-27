#!/bin/bash
# 실제 서버에서 실행할 배포 스크립트

set -e

echo "=========================================="
echo "  ELBIX AIDD 배포 시작"
echo "  도메인: stlogic.aidd.co.kr"
echo "=========================================="
echo ""

# 1. Docker 서비스 확인 및 시작
echo "[1/5] Docker 서비스 확인..."
if ! systemctl is-active --quiet docker; then
    echo "Docker 서비스 시작 중..."
    sudo systemctl start docker
    sleep 3
fi

if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker 데몬에 연결할 수 없습니다."
    echo "다음 명령으로 수동 시작: sudo dockerd"
    exit 1
fi

echo "✅ Docker 준비 완료"
echo ""

# 2. 환경 변수 확인
echo "[2/5] 환경 변수 확인..."
if [ ! -f .env ]; then
    echo "❌ .env 파일이 없습니다."
    exit 1
fi
echo "✅ 환경 변수 파일 확인 완료"
echo ""

# 3. Docker 이미지 빌드
echo "[3/5] Docker 이미지 빌드 중..."
echo "이 작업은 몇 분이 소요될 수 있습니다..."
docker compose build --no-cache
echo "✅ 빌드 완료"
echo ""

# 4. 컨테이너 시작
echo "[4/5] 컨테이너 시작 중..."
docker compose up -d
echo "✅ 컨테이너 시작 완료"
echo ""

# 5. 상태 확인
echo "[5/5] 배포 상태 확인..."
sleep 3
docker compose ps
echo ""

# 로그 확인
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
echo "📋 다음 단계:"
echo "   1. DNS 설정 확인: nslookup stlogic.aidd.co.kr"
echo "   2. SSL 인증서 설정:"
echo "      sudo apt-get install -y certbot python3-certbot-nginx"
echo "      sudo certbot --nginx -d stlogic.aidd.co.kr"
echo "   3. 로그 확인: docker compose logs -f"
echo "   4. 컨테이너 재시작: docker compose restart"
echo ""
