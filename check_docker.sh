#!/bin/bash
echo "=== Docker 환경 확인 ==="
echo ""
echo "1. Docker 소켓 확인:"
ls -la /var/run/docker.sock 2>/dev/null && echo "✅ 소켓 존재" || echo "❌ 소켓 없음"
echo ""
echo "2. Docker 명령어 테스트:"
docker ps 2>&1 | head -3
echo ""
echo "3. Docker 버전:"
docker --version 2>&1
docker compose version 2>&1
echo ""
echo "4. 현재 사용자:"
id
echo ""
echo "5. Docker 그룹 확인:"
getent group docker 2>/dev/null || echo "docker 그룹 없음"
