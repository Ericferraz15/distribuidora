import { render } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from '../theme/ThemeContext.jsx'
import { ToastProvider } from '../components/Toast.jsx'
import { AuthProvider } from '../auth/AuthContext.jsx'
import { fakeToken } from './token.js'

const ACCESS_KEY = 'dm_access_token'
const REFRESH_KEY = 'dm_refresh_token'

// Grava um token de sessão no localStorage antes de montar (simula usuário logado).
export function login(permissao = 'admin', sub = 1) {
  localStorage.setItem(ACCESS_KEY, fakeToken({ permissao, sub }))
  localStorage.setItem(REFRESH_KEY, fakeToken({ permissao, sub, tipo: 'refresh' }))
}

// Monta a UI com todos os providers da app. `route` define a rota inicial;
// `path` permite capturar params se necessário.
export function renderWithProviders(ui, { route = '/', path } = {}) {
  const user = userEvent.setup()
  const result = render(
    <ThemeProvider>
      <ToastProvider>
        <MemoryRouter initialEntries={[route]}>
          <AuthProvider>
            {path ? (
              <Routes>
                <Route path={path} element={ui} />
              </Routes>
            ) : (
              ui
            )}
          </AuthProvider>
        </MemoryRouter>
      </ToastProvider>
    </ThemeProvider>
  )
  return { user, ...result }
}
