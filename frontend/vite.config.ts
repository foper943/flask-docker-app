import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    // В production базовый путь берётся из VITE_BASE_PATH (нужен для GitHub Pages)
    // Vite требует trailing slash, React Router — нет; добавляем здесь
    base: env.VITE_BASE_PATH ? env.VITE_BASE_PATH + '/' : '/',
    plugins: [react()],
    server: {
      host: '0.0.0.0',
      port: 5173,
      proxy: {
        // В dev-режиме Vite проксирует /api и /socket.io → Flask
        '/api': { target: 'http://localhost:5000', changeOrigin: true },
        '/socket.io': { target: 'http://localhost:5000', changeOrigin: true, ws: true },
      },
    },
    preview: {
      host: '0.0.0.0',
      port: 3000,
    },
  }
})
