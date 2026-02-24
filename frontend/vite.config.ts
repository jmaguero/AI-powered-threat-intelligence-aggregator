import { fileURLToPath, URL } from 'node:url'

import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  test: {
    globals: true,
    environment: 'jsdom', // or 'node' if only testing schemas, but 'jsdom' is safe for React
    setupFiles: './src/tests/setup.ts',
  },
})
