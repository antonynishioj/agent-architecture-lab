import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Forward API calls and the progress WebSocket to the FastAPI backend.
      '/api': {
        target: 'http://127.0.0.1:8000',
        ws: true,
      },
    },
  },
})
