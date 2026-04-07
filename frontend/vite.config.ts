import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import basicSsl from '@vitejs/plugin-basic-ssl' // <--- ESTO ES LO QUE FALTA

export default defineConfig({
  plugins: [react(), basicSsl()],
  server: {
    host: true,
    port: 5173
  }
})