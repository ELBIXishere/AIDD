# 빠른 배포 가이드

## 1단계: 서버 준비

```bash
# Docker 및 Docker Compose 설치
sudo apt-get update
sudo apt-get install -y docker.io docker-compose

# Docker 서비스 시작
sudo systemctl start docker
sudo systemctl enable docker
```

## 2단계: 프로젝트 설정

```bash
# 프로젝트 디렉토리로 이동
cd /opt/elbix-aidd  # 또는 원하는 경로

# 환경 변수 설정
cp .env.example .env
nano .env
```

`.env` 파일에서 다음을 수정:

```env
DOMAIN=stlogic.aidd.co.kr
SECRET_KEY=강력한-랜덤-문자열-생성
CORS_ORIGINS=https://stlogic.aidd.co.kr,http://stlogic.aidd.co.kr
SESSION_HTTPS_ONLY=True
```

## 3단계: Nginx 설정

```bash
# nginx/nginx.conf 파일에서 도메인 변경
nano nginx/nginx.conf
# server_name stlogic.aidd.co.kr; 로 변경
```

## 4단계: 배포 실행

```bash
# Docker Compose로 빌드 및 실행
docker-compose up -d --build

# 로그 확인
docker-compose logs -f
```

## 5단계: SSL 인증서 설정 (HTTPS)

```bash
# Certbot 설치
sudo apt-get install -y certbot python3-certbot-nginx

# SSL 인증서 발급
sudo certbot --nginx -d stlogic.aidd.co.kr

# 자동 갱신 테스트
sudo certbot renew --dry-run
```

## 완료!

이제 `https://stlogic.aidd.co.kr`로 접속할 수 있습니다.

자세한 내용은 `DEPLOYMENT.md`를 참고하세요.
