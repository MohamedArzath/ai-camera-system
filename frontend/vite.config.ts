import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
    plugins: [react()],
    server: {
        port: 5173,
        proxy: {
            // HTTP API requests: /api/stream, /api/detect/*, /health, etc.
            '/api': {
                target: 'http://localhost:8001',
                changeOrigin: true,
                // Enable WebSocket proxying for /api/ws
                ws: true,
            },
        },
    },
})
