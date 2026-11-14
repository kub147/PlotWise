import { fileURLToPath, URL } from 'node:url'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// base './' — relative paths, so the build works under any URL (GitHub Pages) together with HashRouter.
export default defineConfig({
  base: './',
  // Static files (favicon and the data copies made by sync-data) live in static/, not in the default public/.
  publicDir: 'static',
  build: {
    // Output goes to build/, not the default dist/. The folder is not emptied before building:
    // on an exFAT drive deleting folders left locked entries and the build failed.
    outDir: 'build',
    emptyOutDir: false,
  },
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
})
