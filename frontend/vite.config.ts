import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    hmr: {
      protocol: 'ws',
      host: 'localhost',
      port: 5173,
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('react-dom') || id.includes('react-router-dom') || (id.includes('/react/') && !id.includes('@chakra'))) {
              return 'vendor-react'
            }
            if (id.includes('@chakra-ui') || id.includes('@emotion')) {
              return 'vendor-chakra'
            }
            if (id.includes('echarts') || id.includes('klinecharts')) {
              return 'vendor-echarts'
            }
            if (id.includes('@tanstack')) {
              return 'vendor-tanstack'
            }
            if (id.includes('axios') || id.includes('date-fns') || id.includes('zustand') || id.includes('zod')) {
              return 'vendor-utils'
            }
            return 'vendor-misc'
          }
        },
      },
    },
  },
})
