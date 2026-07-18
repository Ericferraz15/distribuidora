import { describe, it, expect } from 'vitest'
import { screen, within } from '@testing-library/react'
import Usuarios from './Usuarios.jsx'
import { renderWithProviders, login as fazerLogin } from '../test/utils.jsx'

describe('Usuarios', () => {
  it('lista e cria usuário', async () => {
    fazerLogin('admin', 1)
    const { user } = renderWithProviders(<Usuarios />)

    expect(await screen.findByText('joao')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /novo usuário/i }))
    const dialog = screen.getByRole('dialog')
    const texts = dialog.querySelectorAll('input[type="text"]') // Nome, Telefone
    const senha = dialog.querySelector('input[type="password"]')
    await user.type(texts[0], 'maria')
    await user.type(senha, 'segredo123')
    await user.click(within(dialog).getByRole('button', { name: /salvar/i }))

    expect(await screen.findByText('Usuário criado.')).toBeInTheDocument()
    expect(await screen.findByText('maria')).toBeInTheDocument()
  })

  it('não permite desativar a si mesmo e desativa outro usuário', async () => {
    fazerLogin('admin', 1) // usuário 1 = admin
    const { user } = renderWithProviders(<Usuarios />)
    await screen.findByText('joao')

    // Botão da própria linha (marcada com "você") fica desabilitado.
    const minhaLinha = screen.getByText('você').closest('tr')
    expect(within(minhaLinha).getByRole('button', { name: /desativar/i })).toBeDisabled()

    // Já o de outro usuário funciona.
    const linhaJoao = screen.getByText('joao').closest('tr')
    await user.click(within(linhaJoao).getByRole('button', { name: /desativar/i }))
    expect(await screen.findByText('Usuário desativado.')).toBeInTheDocument()
  })
})
