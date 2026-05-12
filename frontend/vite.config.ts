import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import basicSsl from '@vitejs/plugin-basic-ssl'

export default defineConfig({
  plugins: [react(), basicSsl()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/auth': {
        target: 'https://tars_backend:8000',
        changeOrigin: true,
        secure: false,
      },
      '/api': {
        target: 'https://tars_backend:8000',
        changeOrigin: true,
        secure: false,
      },
      '/start_session': {
        target: 'https://tars_backend:8000',
        changeOrigin: true,
        secure: false,
      },
      '/greeting': {
        target: 'https://tars_backend:8000',
        changeOrigin: true,
        secure: false,
      },
      '/preload_message': {
        target: 'https://tars_backend:8000',
        changeOrigin: true,
        secure: false,
      },
      '/preload_roleplay_message': {
        target: 'https://tars_backend:8000',
        changeOrigin: true,
        secure: false,
      },
      '/stt': {
        target: 'https://tars_backend:8000',
        changeOrigin: true,
        secure: false,
      },
      '/health': {
        target: 'https://tars_backend:8000',
        changeOrigin: true,
        secure: false,
      },
      '/roleplay': {
        target: 'https://tars_backend:8000',
        changeOrigin: true,
        secure: false,
      },
      '/ws': {
        target: 'wss://tars_backend:8000',
        ws: true,
        secure: false,
      },
    }
  }
})