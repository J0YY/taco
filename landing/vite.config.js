import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base must match the GitHub Pages project path: https://j0yy.github.io/taco/
export default defineConfig({
  base: '/taco/',
  plugins: [react()],
  server: { port: 5180, host: true },
})
