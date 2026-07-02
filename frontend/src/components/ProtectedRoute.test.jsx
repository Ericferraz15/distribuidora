import { describe, it, expect } from 'vitest'
import { screen } from '@testing-library/react'
import { Routes, Route } from 'react-router-dom'
import ProtectedRoute from './ProtectedRoute.jsx'
import { renderWithProviders, login as fazerLogin } from '../test/utils.jsx'

const arvore = (
  <Routes>
    <Route path="/login" element={<div>LOGIN</div>} />
    <Route path="/operacao" element={<div>OPERACAO</div>} />
    <Route path="/secreto" element={<ProtectedRoute><div>SECRETO</div></ProtectedRoute>} />
    <Route path="/admin" element={<ProtectedRoute adminOnly><div>PAINEL ADMIN</div></ProtectedRoute>} />
  </Routes>
)

describe('ProtectedRoute', () => {
  it('sem autenticação redireciona para /login', () => {
    renderWithProviders(arvore, { route: '/secreto' })
    expect(screen.getByText('LOGIN')).toBeInTheDocument()
  })

  it('rota adminOnly bloqueia funcionário (manda para /operacao)', () => {
    fazerLogin('funcionario')
    renderWithProviders(arvore, { route: '/admin' })
    expect(screen.getByText('OPERACAO')).toBeInTheDocument()
  })

  it('permite admin em rota adminOnly', () => {
    fazerLogin('admin')
    renderWithProviders(arvore, { route: '/admin' })
    expect(screen.getByText('PAINEL ADMIN')).toBeInTheDocument()
  })

  it('permite qualquer autenticado em rota protegida comum', () => {
    fazerLogin('funcionario')
    renderWithProviders(arvore, { route: '/secreto' })
    expect(screen.getByText('SECRETO')).toBeInTheDocument()
  })
})
