import { describe, it, expect } from 'vitest'
import { act } from 'react'
import { screen, waitFor } from '@testing-library/react'
import { useAuth } from './AuthContext.jsx'
import { renderWithProviders, login as fazerLogin } from '../test/utils.jsx'

function Sonda() {
  const { user, login, logout } = useAuth()
  return (
    <div>
      <span data-testid="perm">{user?.permissao ?? 'anon'}</span>
      <button onClick={() => login('admin', 'x')}>entrar</button>
      <button onClick={logout}>sair</button>
    </div>
  )
}

describe('AuthContext', () => {
  it('login popula o usuário a partir do token e logout limpa', async () => {
    const { user } = renderWithProviders(<Sonda />)
    expect(screen.getByTestId('perm')).toHaveTextContent('anon')

    await user.click(screen.getByText('entrar'))
    await waitFor(() => expect(screen.getByTestId('perm')).toHaveTextContent('admin'))

    await user.click(screen.getByText('sair'))
    await waitFor(() => expect(screen.getByTestId('perm')).toHaveTextContent('anon'))
  })

  it('inicia autenticado com token salvo e desloga no evento auth:logout', async () => {
    fazerLogin('funcionario', 2)
    renderWithProviders(<Sonda />)
    expect(screen.getByTestId('perm')).toHaveTextContent('funcionario')

    act(() => window.dispatchEvent(new Event('auth:logout')))
    await waitFor(() => expect(screen.getByTestId('perm')).toHaveTextContent('anon'))
  })
})
