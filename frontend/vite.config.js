import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Prefixos servidos pela Distribuidora API (FastAPI em 127.0.0.1:8000).
// Em desenvolvimento o Vite faz proxy para evitar CORS e manter as URLs
// relativas ("/auth/login", "/produtos", ...). Em producao, defina
// VITE_API_URL apontando para a API e o proxy deixa de ser necessario.
const API_TARGET = process.env.VITE_API_URL || 'http://127.0.0.1:8000'
const PREFIXOS = ['/auth', '/usuarios', '/turnos', '/caixa', '/transacoes', '/produtos', '/dashboard']

export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // escuta em 0.0.0.0 — acessivel por outros aparelhos da rede local
    port: 3000,
    strictPort: true, // falha claro se a 3000 estiver ocupada (em vez de trocar de porta)
    allowedHosts: true, // aceita acesso por qualquer host/IP (Vite 5.4+)
    proxy: Object.fromEntries(
      PREFIXOS.map((p) => [p, { target: API_TARGET, changeOrigin: true }])
    ),
  },
  // Configuracao dos testes (Vitest). Roda em jsdom com globals estilo Jest.
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.js'],
    css: true,
    restoreMocks: true,
    // O fetch do Node exige URL absoluta; fixamos a base da API e alinhamos a URL
    // do jsdom com ela para o MSW resolver os handlers relativos na mesma origem.
    env: { VITE_API_URL: 'http://localhost:8000' },
    environmentOptions: { jsdom: { url: 'http://localhost:8000' } },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      include: ['src/**/*.{js,jsx}'],
      exclude: ['src/test/**', 'src/main.jsx', 'src/**/*.test.{js,jsx}'],
    },
  },
})
