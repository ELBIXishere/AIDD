# DooD (Docker-out-of-Docker) 배포 가이드

## 현재 상황

현재 환경이 Docker 컨테이너 안에 있으므로, 호스트의 Docker 소켓을 사용하여 배포할 수 있습니다.

## 필수 조건

1. **호스트의 Docker 데몬이 실행 중이어야 함**
2. **컨테이너가 Docker 소켓에 접근 권한이 있어야 함**

## 해결 방법

### 방법 1: 호스트에서 Docker 데몬 확인 및 시작

호스트 서버에서:

```bash
# Docker 데몬 상태 확인
sudo systemctl status docker

# Docker 데몬 시작 (중지된 경우)
sudo systemctl start docker

# 확인
sudo docker ps
```

### 방법 2: 컨테이너를 Docker 소켓과 함께 실행

현재 컨테이너가 Docker 소켓 없이 실행되었다면, 
호스트에서 컨테이너를 다시 시작할 때 다음 옵션 추가:

```bash
docker run -it \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd):/workspace \
  your-image
```

### 방법 3: Docker 소켓 권한 조정 (임시)

호스트에서:

```bash
# 임시로 모든 사용자가 접근 가능하도록 (보안 주의!)
sudo chmod 666 /var/run/docker.sock
```

## 배포 실행

호스트의 Docker가 준비되면:

```bash
cd /root/elbix_aidd
./DOOD_DEPLOY.sh
```

또는 직접:

```bash
docker compose up -d --build
```

## 확인

```bash
# 컨테이너 상태
docker compose ps

# 로그 확인
docker compose logs -f
```
