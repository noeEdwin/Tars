import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import basicSsl from '@vitejs/plugin-basic-ssl'
// Change if your backend server is running on a different port or URL for example tars_backend:8000
export default defineConfig({
  plugins: [react(), basicSsl()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/auth': {
        target: 'https://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/api': {
        target: 'https://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/start_session': {
        target: 'https://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/greeting': {
        target: 'https://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/preload_message': {
        target: 'https://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/stt': {
        target: 'https://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/health': {
        target: 'https://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/roleplay': {
        target: 'https://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/ws': {
        target: 'wss://localhost:8000',
        ws: true,
        secure: false,
      },
    }
  }
})