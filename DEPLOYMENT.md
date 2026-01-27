# ELBIX AIDD 외부 배포 가이드

이 문서는 ELBIX AIDD 애플리케이션을 외부 도메인(예: `stlogic.aidd.co.kr`)으로 배포하는 방법을 설명합니다.

## 사전 준비사항

1. **서버 준비**
   - Ubuntu 20.04 이상 또는 CentOS 7 이상
   - Docker 및 Docker Compose 설치
   - 도메인 DNS 설정 완료

2. **도메인 설정**
   - 도메인을 서버 IP로 A 레코드 설정
   - 예: `stlogic.aidd.co.kr` → 서버 IP 주소

3. **포트 확인**
   - 80 (HTTP)
   - 443 (HTTPS)
   - 8000 (백엔드, 내부 전용)

## 배포 단계

### 1. 서버에 프로젝트 클론

```bash
# 서버에 접속
ssh user@your-server-ip

# 프로젝트 디렉토리로 이동
cd /opt  # 또는 원하는 디렉토리

# Git에서 클론 (또는 파일 업로드)
git clone <repository-url> elbix-aidd
cd elbix-aidd
```

### 2. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집
nano .env
```

`.env` 파일에서 다음 항목을 수정하세요:

```env
# 도메인 설정
DOMAIN=stlogic.aidd.co.kr

# 보안 키 (반드시 변경!)
SECRET_KEY=your-very-secure-random-key-here

# 디버그 모드 (운영 환경에서는 False)
DEBUG=False

# WFS 서버 URL (내부 네트워크 주소로 변경 가능)
GIS_WFS_URL=http://192.168.0.71:8881/orange/wfs?GDX=AI_FAC.xml
BASE_WFS_URL=http://192.168.0.71:8881/orange/wfs?GDX=AI_BASE.xml
```

### 3. Nginx 설정 수정

```bash
# nginx/nginx.conf 파일 편집
nano nginx/nginx.conf
```

`server_name`을 실제 도메인으로 변경:

```nginx
server_name stlogic.aidd.co.kr;  # 여기를 실제 도메인으로 변경
```

### 4. CORS 및 세션·쿠키 연결 (로그인/설계 동작 필수)

로그인·설계 실행이 되려면 **브라우저 접속 주소(Origin)**가 백엔드 CORS 허용 목록에 포함되고, **Nginx가 Cookie를 백엔드로 넘겨야** 합니다.

**CORS_ORIGINS (.env 또는 docker-compose 환경변수)**  
- 사용자가 접속하는 URL과 **정확히 일치**해야 함 (프로토콜·호스트·포트 모두).
- 예: `http://stlogic.aidd.co.kr`, `http://192.168.0.64`, `https://stlogic.aidd.co.kr` 등. 쉼표로 구분.
- docker-compose 기본값에는 `http://stlogic.aidd.co.kr`, `http://192.168.0.64` 등이 포함되어 있음.  
  다른 주소로 접속하면 `.env`에 추가:
  ```env
  CORS_ORIGINS=http://실제접속주소,https://실제접속주소
  ```

**Nginx Cookie 전달**  
- `nginx/nginx.conf`의 `/api/` location에 `proxy_set_header Cookie $http_cookie;`가 있어야 세션 쿠키가 백엔드까지 전달됨. (이미 포함됨)

**프론트엔드 API 주소**  
- 배포 시 `VITE_API_URL=/api/v1`(상대 경로)로 두면, Nginx가 같은 호스트에서 `/api`를 백엔드로 프록시하므로 세션·쿠키가 정상 동작함.  
- `http://다른서버:8000/api/v1`처럼 절대 URL을 쓰면 크로스 오리진이 되어 쿠키가 안 붙을 수 있음.

### 5. Docker 이미지 빌드 및 실행

```bash
# Docker Compose로 빌드 및 실행
docker-compose up -d --build

# 로그 확인
docker-compose logs -f
```

### 6. SSL 인증서 설정 (HTTPS)

Let's Encrypt를 사용한 무료 SSL 인증서 설정:

```bash
# Certbot 설치
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# SSL 인증서 발급 (Nginx 플러그인 사용)
sudo certbot --nginx -d stlogic.aidd.co.kr

# 자동 갱신 설정
sudo certbot renew --dry-run
```

인증서 발급 후 `nginx/nginx.conf`의 SSL 설정을 활성화:

```nginx
listen 443 ssl http2;
ssl_certificate /etc/letsencrypt/live/stlogic.aidd.co.kr/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/stlogic.aidd.co.kr/privkey.pem;
```

그리고 HTTP → HTTPS 리다이렉트 활성화:

```nginx
server {
    listen 80;
    server_name stlogic.aidd.co.kr;
    return 301 https://$server_name$request_uri;
}
```

### 7. 방화벽 설정

```bash
# UFW 사용 시
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# 또는 iptables 사용 시
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
```

## 운영 관리

### 컨테이너 관리

```bash
# 컨테이너 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f nginx

# 컨테이너 재시작
docker-compose restart

# 컨테이너 중지
docker-compose stop

# 컨테이너 시작
docker-compose start

# 컨테이너 중지 및 삭제
docker-compose down
```

### 업데이트 배포

```bash
# 코드 업데이트
git pull

# 이미지 재빌드 및 재시작
docker-compose up -d --build

# 프론트엔드만 재빌드
docker-compose up -d --build frontend
```

## 문제 해결

### 1. 도메인 접속 불가

- DNS 설정 확인: `nslookup stlogic.aidd.co.kr`
- 방화벽 포트 확인: `sudo ufw status`
- Nginx 로그 확인: `docker-compose logs nginx`

### 2. API 호출 실패

- CORS 설정 확인: `app/main.py`의 `allow_origins`
- 백엔드 로그 확인: `docker-compose logs backend`
- 네트워크 확인: `docker-compose ps`

### 3. 프론트엔드 빌드 실패

- Node 버전 확인: `node --version` (18 이상 필요)
- 의존성 재설치: `cd frontend && npm ci`

## 보안 권장사항

1. **환경 변수 보호**
   - `.env` 파일은 절대 Git에 커밋하지 않기
   - `.gitignore`에 `.env` 추가 확인

2. **SSL/TLS 사용**
   - 운영 환경에서는 반드시 HTTPS 사용
   - HTTP → HTTPS 리다이렉트 설정

3. **세션 보안**
   - `SECRET_KEY`는 강력한 랜덤 문자열 사용
   - `https_only=True` 설정 (HTTPS 사용 시)

4. **API 문서 접근 제한**
   - 운영 환경에서는 `/docs`, `/redoc` 접근 차단 권장
