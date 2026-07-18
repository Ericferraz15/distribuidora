import { describe, it, expect } from 'vitest'
import { http, HttpResponse } from 'msw'
import { screen } from '@testing-library/react'
import { Routes, Route } from 'react-router-dom'
import Login from './Login.jsx'
import { server } from '../test/server.js'
import { renderWithProviders } from '../test/utils.jsx'

const arvore = (
  <Routes>
    <Route path="/login" element={<Login />} />
    <Route path="/dashboard" element={<div>DASHBOARD</div>} />
    <Route path="/operacao" element={<div>OPERACAO</div>} />
  </Routes>
)

describe('Login', () => {
  it('autentica e navega para o painel do admin', async () => {
    const { user, container } = renderWithProviders(arvore, { route: '/login' })
    await user.type(container.querySelector('input[type="text"]'), 'admin')
    await user.type(container.querySelector('input[type="password"]'), 'admin123')
    await user.click(screen.getByRole('button', { name: /entrar/i }))

    expect(await screen.findByText('DASHBOARD')).toBeInTheDocument()
  })

  it('mostra alerta de erro em credenciais inválidas', async () => {
    server.use(
      http.post('/auth/login', () =>
        HttpResponse.json({ detail: 'Credenciais inválidas' }, { status: 401 })
      )
    )
    const { user, container } = renderWithProviders(arvore, { route: '/login' })
    await user.type(container.querySelector('input[type="text"]'), 'admin')
    await user.type(container.querySelector('input[type="password"]'), 'errada')
    await user.click(screen.getByRole('button', { name: /entrar/i }))

    expect(await screen.findByText('Credenciais inválidas')).toBeInTheDocument()
  })
})
