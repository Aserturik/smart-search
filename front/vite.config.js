import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

export default defineConfig({
  plugins: [react()],
  base: '/',
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    cors: true,
    hmr: {
      clientPort: 5173,
      host: '0.0.0.0',
    },
    proxy: {
      '/ws': {
        target: 'ws://localhost:15674',
        ws: true,
      }
    }
  }
})
