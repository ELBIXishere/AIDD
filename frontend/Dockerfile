# 프론트엔드 빌드용 Dockerfile
FROM node:18-alpine AS builder

# 작업 디렉토리 설정
WORKDIR /app

# package.json과 package-lock.json 복사
COPY package*.json ./

# 의존성 설치
RUN npm ci

# 소스 코드 복사
COPY . .

# 환경 변수 설정 (빌드 시점에 주입)
ARG VITE_API_URL=/api/v1
ENV VITE_API_URL=$VITE_API_URL

# 프로덕션 빌드
RUN npm run build

# Nginx를 사용한 정적 파일 서빙
FROM nginx:alpine

# 빌드된 파일을 nginx 디렉토리로 복사
COPY --from=builder /app/dist /usr/share/nginx/html

# 포트 노출
EXPOSE 80

# Nginx 실행
CMD ["nginx", "-g", "daemon off;"]
