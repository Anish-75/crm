import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
// vite.config.ts
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
})
