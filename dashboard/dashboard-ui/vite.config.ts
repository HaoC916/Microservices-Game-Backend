import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Production build is served from GitHub Pages at
// https://haoc916.github.io/Microservices-Game-Backend/ ; dev runs at root.
export default defineConfig(({ command }) => ({
  base: command === 'build' ? '/Microservices-Game-Backend/' : '/',
  plugins: [react()],
}))
