import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterAll, afterEach, beforeAll } from 'vitest'
import { server } from './server.js'
import { resetDb } from './handlers.js'

// Servidor MSW ativo durante toda a bateria. `onUnhandledRequest: 'error'` garante
// que nenhuma chamada de rede real escape sem mock.
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))

afterEach(() => {
  server.resetHandlers()
  cleanup()
  localStorage.clear()
  resetDb()
})

afterAll(() => server.close())
