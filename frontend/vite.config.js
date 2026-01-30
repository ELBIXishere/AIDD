import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',  // 외부 접속 허용
    port: 3000,
    strictPort: true,  // 포트 고정 (3000 사용 불가 시 에러)
    allowedHosts: ['stlogic.iptime.org'], // 외부 호스트 허용
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        // 세션/쿠키: 요청 시 Cookie 전달, 백엔드가 Set-Cookie 시 브라우저 접속 호스트와 맞추기 위해 Host 전달
        configure: (proxy) => {
          proxy.on('proxyReq', (proxyReq, req) => {
            if (req.headers.cookie) {
              proxyReq.setHeader('Cookie', req.headers.cookie)
            }
            // 브라우저 접속 호스트(예: 192.168.0.64:3000) 전달 → 세션 쿠키 scope 일치
            if (req.headers.host) {
              proxyReq.setHeader('X-Forwarded-Host', req.headers.host)
            }
          })
        },
      }
    }
  }
})
