import path from 'path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Dev server port and API proxy target are env-overridable so the app can run
// alongside other local projects that may already hold the defaults.
const port = Number(process.env.VITE_PORT) || 5173
const apiTarget = process.env.VITE_API_TARGET || 'http://localhost:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port,
    proxy: {
      // Proxy API calls to the FastAPI backend during development so the
      // frontend can use same-origin '/api/...' paths (no CORS dance in dev).
      '/api': {
        target: apiTarget,
        changeOrigin: true,
      },
    },
  },
})
