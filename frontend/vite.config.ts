import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // Optionally, remove /api prefix if backend does not expect it:
        // rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
