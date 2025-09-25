import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,  // 确保端口与控制台显示的前端端口一致
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
        // 增加超时设置，避免长时间请求被中断
        timeout: 60000
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets'
  }
})
