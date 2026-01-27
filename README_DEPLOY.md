# 배포 실행 가이드

## 현재 상황

✅ **완료된 작업:**
- Docker 및 Docker Compose 설치
- 환경 변수 파일 (.env) 생성
- Nginx 설정 확인
- 배포 스크립트 생성

⚠️ **현재 환경 제한:**
- Docker 데몬이 자동으로 시작되지 않음 (권한/환경 제한)

## 실제 서버에서 배포하는 방법

### 방법 1: 배포 스크립트 사용 (권장)

```bash
cd /root/elbix_aidd
./deploy.sh
```

### 방법 2: 수동 배포

```bash
# 1. Docker 서비스 시작
sudo systemctl start docker
# 또는
sudo dockerd &

# 2. Docker Compose 실행
cd /root/elbix_aidd
docker compose up -d --build

# 3. 상태 확인
docker compose ps
docker compose logs -f
```

## SSL 인증서 설정 (HTTPS - 무료)

```bash
# Certbot 설치
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# SSL 인증서 발급
sudo certbot --nginx -d stlogic.aidd.co.kr

# 자동 갱신 설정
sudo certbot renew --dry-run
```

## DNS 설정 확인

도메인 `stlogic.aidd.co.kr`이 서버 IP (`14.63.58.144`)로 설정되어 있는지 확인:

```bash
nslookup stlogic.aidd.co.kr
```

## 문제 해결

### Docker 데몬이 시작되지 않을 때

```bash
# 로그 확인
sudo journalctl -u docker
# 또는
cat /var/log/docker.log

# 수동 시작
sudo dockerd
```

### 포트가 이미 사용 중일 때

```bash
# 포트 확인
sudo netstat -tlnp | grep -E ":(80|443|8000)"
# 프로세스 종료
sudo kill -9 <PID>
```

## 접속 확인

배포 후 다음 URL로 접속:
- HTTP: http://stlogic.aidd.co.kr
- HTTPS: https://stlogic.aidd.co.kr (SSL 설정 후)
