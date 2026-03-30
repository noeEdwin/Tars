import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
// @ts-ignore
import basicSsl from '@vitejs/plugin-basic-ssl'

export default defineConfig({
  plugins: [react(), basicSsl()],
  server: { host: true }
})
