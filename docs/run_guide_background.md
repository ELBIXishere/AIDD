# 백그라운드 실행 및 배포 가이드 (Docker 미사용)

이 문서는 Docker 환경을 사용할 수 없을 때, 터미널 종료 후에도 서버가 중단되지 않도록 `nohup`을 이용하여 백그라운드에서 프로세스를 실행하는 방법을 설명합니다.

## 1. 백엔드 (FastAPI) 실행

루트 디렉토리(`/root/elbix_aidd`)에서 실행합니다.

### 실행 명령어
```bash
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
```
- `nohup`: 터미널이 종료되어도 프로세스를 유지합니다.
- `> backend.log 2>&1`: 모든 출력과 에러 메시지를 `backend.log`에 기록합니다.
- `&`: 백그라운드 프로세스로 실행합니다.

### 실행 확인
```bash
ps -ef | grep uvicorn
```

### 로그 확인
```bash
tail -f backend.log
```

---

## 2. 프론트엔드 (React + Vite) 실행

`frontend` 디렉토리에서 실행합니다.

### 실행 명령어
```bash
cd /root/elbix_aidd/frontend
# 의존성 설치 (필요한 경우)
npm install
# 백그라운드 실행
nohup npm run dev -- --host 0.0.0.0 > frontend.log 2>&1 &
```

### 실행 확인
```bash
ps -ef | grep vite
```

### 로그 확인
```bash
tail -f frontend.log
```

---

## 3. 프로세스 종료 방법

서버를 재시작하거나 중단해야 할 경우, 다음 명령어로 프로세스 ID(PID)를 찾아 종료합니다.

### 백엔드 종료
```bash
kill $(pgrep -f uvicorn)
```

### 프론트엔드 종료
```bash
kill $(pgrep -f vite)
```

---

## 4. 요약 가이드

| 서비스 | 실행 디렉토리 | 실행 명령어 (백그라운드) | 로그 파일 |
| :--- | :--- | :--- | :--- |
| **백엔드** | `/root/elbix_aidd` | `nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &` | `backend.log` |
| **프론트엔드** | `/root/elbix_aidd/frontend` | `nohup npm run dev -- --host 0.0.0.0 > frontend.log 2>&1 &` | `frontend.log` |
