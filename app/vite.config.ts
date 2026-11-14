import { fileURLToPath, URL } from 'node:url'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// base './' — ścieżki względne, więc build działa pod dowolnym adresem (GitHub Pages) razem z HashRouter.
export default defineConfig({
  base: './',
  // Pliki statyczne (favicon i kopie danych z sync-data) leżą w static/, nie w domyślnym public/.
  publicDir: 'static',
  build: {
    // Wynik trafia do build/, a nie do domyślnego dist/. Katalogu nie czyścimy przed budowaniem:
    // na dysku exFAT usuwanie folderów zostawiało zablokowane wpisy i build się wywracał.
    outDir: 'build',
    emptyOutDir: false,
  },
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
})
