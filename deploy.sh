#!/bin/bash
# ELBIX AIDD 배포 스크립트

set -e

echo "=== ELBIX AIDD 배포 시작 ==="

# 1. 환경 변수 확인
if [ ! -f .env ]; then
    echo "❌ .env 파일이 없습니다. .env.example을 복사하여 생성하세요."
    exit 1
fi

# 2. Docker 서비스 시작
echo "📦 Docker 서비스 시작 중..."
sudo systemctl start docker || sudo dockerd &
sleep 3

# 3. Docker Compose로 빌드 및 실행
echo "🔨 Docker 이미지 빌드 중..."
docker compose up -d --build

# 4. 컨테이너 상태 확인
echo "📊 컨테이너 상태 확인..."
docker compose ps

# 5. 로그 확인
echo "📝 최근 로그 확인..."
docker compose logs --tail=20

echo ""
echo "✅ 배포 완료!"
echo "🌐 접속 URL: http://stlogic.aidd.co.kr"
echo ""
echo "다음 단계:"
echo "1. DNS 설정 확인 (stlogic.aidd.co.kr → 서버 IP)"
echo "2. SSL 인증서 설정: sudo certbot --nginx -d stlogic.aidd.co.kr"
echo "3. 로그 확인: docker compose logs -f"
